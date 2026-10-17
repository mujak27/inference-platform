#!/usr/bin/env python3
"""Real endpoint test; client arrival times are not server-side token timings."""
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--model", default="Qwen/Qwen3-1.7B")
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
    with urllib.request.urlopen(request, timeout=180) as response:
        if response.headers.get_content_type() != "text/event-stream":
            raise ValueError("Endpoint did not return an SSE stream")
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
    }))


if __name__ == "__main__":
    main()
