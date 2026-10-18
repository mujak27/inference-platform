#!/usr/bin/env python3
"""Render the pinned candidates offline; never download artifacts or contact an API."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import tempfile

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHART_SHA256 = 'd5d94816d4075d56028d937e2134d66bc561b2d752259b18f01084b4d7f1602b'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', choices=('real', 'sim'), required=True)
    parser.add_argument('--chart', type=Path, default=ROOT / '.local/llmd/llm-d-router-standalone-v0.11.0.tgz')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.chart.is_file():
        parser.error('missing chart archive; acquire the approved pinned chart separately')
    if hashlib.sha256(args.chart.read_bytes()).hexdigest() != CHART_SHA256:
        parser.error('chart archive checksum mismatch; refusing to render')
    synthetic = args.candidate == 'sim'
    release, namespace = ('llmd-sim', 'llmd-sim') if synthetic else ('llmd', 'inference')
    values = ROOT / 'apps/llmd' / ('simulator/router-values.yaml' if synthetic else 'candidate/values.yaml')
    try:
        text = subprocess.check_output([
            'helm', 'template', release, str(args.chart.resolve()), '--namespace', namespace,
            '--kube-version', '1.35.0', '--values', str(values)], text=True, cwd=ROOT, timeout=60)
        resources = [r for r in yaml.safe_load_all(text) if r]
        if synthetic:
            text = subprocess.check_output(['kubectl', 'kustomize', 'apps/llmd/simulator'],
                                           text=True, cwd=ROOT, timeout=60)
            resources.extend(r for r in yaml.safe_load_all(text) if r)
        else:
            # The pinned chart includes unused objective/rewrite reads. Own discovery scope explicitly.
            resources = [r for r in resources if r['kind'] not in ('Role', 'RoleBinding')]
            resources.extend(yaml.safe_load_all((ROOT / 'apps/llmd/candidate/discovery-rbac.yaml').read_text()))
        if not resources:
            raise ValueError('empty chart render')
        output = args.output or ROOT / ('.local/llmd-sim/rendered.yaml' if synthetic else '.local/llmd/rendered.yaml')
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', dir=output.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(yaml.safe_dump_all(resources, sort_keys=False))
            temporary.replace(output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    except (OSError, ValueError, yaml.YAMLError, subprocess.SubprocessError) as error:
        parser.exit(1, f'render failed: {error}\n')


if __name__ == '__main__':
    main()
