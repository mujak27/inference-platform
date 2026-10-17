#!/usr/bin/env python3
"""Extract validation schemas from the exact Argo CD CRDs being bootstrapped."""
import json
from pathlib import Path
import sys

import yaml


def extract(documents):
    schemas = {}
    for document in documents:
        if not document or document.get("kind") != "CustomResourceDefinition":
            continue
        spec = document["spec"]
        if spec["group"] != "argoproj.io":
            continue
        for version in spec["versions"]:
            if version["name"] == "v1alpha1" and version["served"]:
                schemas[spec["names"]["kind"].lower()] = version["schema"]["openAPIV3Schema"]
    if not {"application", "appproject"}.issubset(schemas):
        raise ValueError("Pinned Argo CD manifest lacks Application/AppProject schemas")
    return schemas


if __name__ == "__main__":
    source, destination = map(Path, sys.argv[1:])
    destination.mkdir(parents=True, exist_ok=True)
    for kind, schema in extract(yaml.safe_load_all(source.read_text())).items():
        (destination / f"{kind}.json").write_text(json.dumps(schema))
