#!/usr/bin/env python3
"""Real endpoint test; client arrival times are not server-side token timings.

--require-routed only checks EPP's response-path header (x-went-into-resp-headers:
true); full real-backend attribution also correlates the request in the live vllm
pod (kubectl -n inference logs / /metrics).
"""
import argparse
import json
import time
import urllib.request


def content_chunks(lines):
    # vLLM's OpenAI endpoint emits one JSON object per SSE data line.
    for line in lines:
        if not line.startswith(b"data:"):
            continue
        data = line[5:].strip()
        if data == b"[DONE]":
            return
        event = json.loads(data)
        if "error" in event:
            raise ValueError(f"Server returned an error: {event['error']}")
        for choice in event.get("choices", []):
            text = choice.get("delta", {}).get("content")
            if text:
                yield text
    raise ValueError("Stream ended without [DONE]")


def check_response_headers(headers, require_routed=False):
    if headers.get_content_type() != "text/event-stream":
        raise ValueError("Endpoint did not return an SSE stream")
    routed = (headers.get("x-went-into-resp-headers") or "").strip().lower() == "true"
    if require_routed and not routed:
        raise ValueError("Endpoint response was not routed through the gateway "
                         "(x-went-into-resp-headers: true required)")
    return {"routed": routed, "server": headers.get("server", "")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--model", default="Qwen/Qwen3-1.7B")
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--require-routed", action="store_true",
                        help="fail unless the gateway added x-went-into-resp-headers: true")
    args = parser.parse_args()
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": "Briefly explain what a GPU does."}],
        "stream": True,
        "max_tokens": 64,
        "temperature": 0,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    request = urllib.request.Request(
        args.base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
    )
    start = time.monotonic()
    first = None
    count = 0
    output = ""
    with urllib.request.urlopen(request, timeout=args.timeout) as response:
        meta = check_response_headers(response.headers, args.require_routed)
        for text in content_chunks(response):
            if first is None:
                first = time.monotonic() - start
            count += 1
            output += text
            print(text, end="", flush=True)
    elapsed = time.monotonic() - start
    if not output.strip():
        raise ValueError("No nonempty model output received")
    print("\n" + json.dumps({
        "first_content_seconds": first,
        "end_to_end_seconds": elapsed,
        "content_chunks": count,
        "stream_completed": True,
        "routed": meta["routed"],
        "server": meta["server"],
    }))


if __name__ == "__main__":
    main()
