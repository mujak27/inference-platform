#!/usr/bin/env python3
"""Extract validation schemas from the bootstrap and separately installed CRDs."""
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


def extract_extra(documents):
    # Additional CRDs installed separately (e.g. the pinned GAIE InferencePool) are
    # validated with their own served v1 schema, not the Argo CD one. kubeconform
    # only applies -strict to schemas that already forbid unknown properties, so
    # mark every object that declares properties as closed.
    def strict(value):
        if isinstance(value, dict):
            if "properties" in value:
                value.setdefault("additionalProperties", False)
            for child in value.values():
                strict(child)
        elif isinstance(value, list):
            for child in value:
                strict(child)

    schemas = {}
    for document in documents:
        if not document or document.get("kind") != "CustomResourceDefinition":
            continue
        for version in document["spec"]["versions"]:
            if version["name"] == "v1" and version["served"]:
                schema = version["schema"]["openAPIV3Schema"]
                strict(schema)
                schemas[document["spec"]["names"]["kind"].lower()] = schema
    if not schemas:
        raise ValueError("Additional CRD input lacks a served v1 schema")
    return schemas


if __name__ == "__main__":
    source, destination, *extra = map(Path, sys.argv[1:])
    destination.mkdir(parents=True, exist_ok=True)
    schemas = extract(yaml.safe_load_all(source.read_text()))
    for path in extra:
        schemas.update(extract_extra(yaml.safe_load_all(path.read_text())))
    for kind, schema in schemas.items():
        (destination / f"{kind}.json").write_text(json.dumps(schema))
