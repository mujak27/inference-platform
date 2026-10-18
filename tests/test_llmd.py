"""Source-only contracts; fixtures/fake tools are not candidate-runtime evidence."""
from pathlib import Path
import os
import sys
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class RenderCommandTests(unittest.TestCase):
    def test_failed_render_preserves_previous_complete_output(self):
        chart = os.environ.get('LLMD_CHART', str(ROOT / '.local/llmd/llm-d-router-standalone-v0.11.0.tgz'))
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            helm = directory / 'helm'
            helm.write_text('#!/bin/sh\nprintf "partial output"\nexit 3\n')
            helm.chmod(0o755)
            output = directory / 'rendered.yaml'
            output.write_text('previous complete render')
            result = subprocess.run(
                ['bash', str(ROOT / 'scripts/render-llmd.sh'), '--chart', chart, '--output', str(output)],
                env=dict(os.environ, PATH=str(directory) + os.pathsep + os.environ['PATH']),
                text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('render failed', result.stderr)
            self.assertEqual(output.read_text(), 'previous complete render')

    def test_validator_rejects_missing_input_instead_of_skipping(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'scripts/validate-llmd.py'), '--candidate',
                 'real', '--rendered', str(Path(directory) / 'absent.yaml')],
                text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('missing rendered input', result.stderr)

    def test_real_render_uses_current_sources_and_minimal_discovery_rbac(self):
        chart = os.environ.get('LLMD_CHART', str(ROOT / '.local/llmd/llm-d-router-standalone-v0.11.0.tgz'))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'rendered.yaml'
            result = subprocess.run(
                ['bash', str(ROOT / 'scripts/render-llmd.sh'), '--chart', chart,
                 '--output', str(output)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            resources = list(yaml.safe_load_all(output.read_text()))
            roles = [r for r in resources if r['kind'] == 'Role']
            self.assertEqual(len(roles), 1)
            self.assertEqual(roles[0]['rules'], [
                {'apiGroups': [''], 'resources': ['pods'], 'verbs': ['get', 'list', 'watch']},
                {'apiGroups': ['inference.networking.k8s.io'], 'resources': ['inferencepools'],
                 'verbs': ['get', 'list', 'watch']}])
            pool, = [r for r in resources if r['kind'] == 'InferencePool']
            self.assertEqual(pool['spec']['selector']['matchLabels'], {'app.kubernetes.io/name': 'vllm'})

    def test_missing_chart_fails_without_publishing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'rendered.yaml'
            result = subprocess.run(
                ['bash', str(ROOT / 'scripts/render-llmd.sh'), '--chart',
                 str(Path(directory) / 'absent.tgz'), '--output', str(output)],
                text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('chart archive', result.stderr)
            self.assertFalse(output.exists())


class ValidatorCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.chart = os.environ.get('LLMD_CHART', str(ROOT / '.local/llmd/llm-d-router-standalone-v0.11.0.tgz'))
        cls.inputs = {}
        for candidate, script in (('real', 'render-llmd.sh'), ('sim', 'render-llmd-sim.sh')):
            output = Path(cls.directory.name) / f'{candidate}.yaml'
            subprocess.run(['bash', str(ROOT / 'scripts' / script), '--chart', cls.chart,
                            '--output', str(output)], check=True, capture_output=True, text=True)
            cls.inputs[candidate] = output

    def validate(self, candidate, path, policy_only=True):
        return subprocess.run([
            sys.executable, '-B', str(ROOT / 'scripts/validate-llmd.py'),
            '--candidate', candidate, '--rendered', str(path), '--chart', self.chart,
        ] + (['--policy-only'] if policy_only else []), text=True, capture_output=True)

    def test_current_candidates_pass_source_policy_not_runtime_qualification(self):
        for candidate, path in self.inputs.items():
            with self.subTest(candidate=candidate):
                result = self.validate(candidate, path)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('POLICY ONLY', result.stdout)
                self.assertIn('PENDING', result.stdout)

    def test_request_path_fail_open_is_rejected(self):
        resources = list(yaml.safe_load_all(self.inputs['sim'].read_text()))
        config = next(r for r in resources if 'envoy.yaml' in r.get('data', {}))
        config['data']['envoy.yaml'] = config['data']['envoy.yaml'].replace(
            'failure_mode_allow: false', 'failure_mode_allow: true')
        path = Path(self.directory.name) / 'fail-open.yaml'
        path.write_text(yaml.safe_dump_all(resources))
        result = self.validate('sim', path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('fail-closed', result.stderr)

    def test_envoy_bootstrap_cli_overrides_are_rejected(self):
        override = 'admin: {address: {socket_address: {address: 0.0.0.0, port_value: 19000}}}'
        for extra in (['--config-yaml', override], ['--config-yaml=' + override],
                      ['--config-path=/tmp/other.yaml'], ['-c', '/tmp/other.yaml']):
            with self.subTest(extra=extra):
                resources = list(yaml.safe_load_all(self.inputs['sim'].read_text()))
                router = next(r for r in resources if r['kind'] == 'Deployment' and
                              r['metadata']['name'] == 'llmd-sim-epp')
                proxy = next(c for c in router['spec']['template']['spec']['containers']
                             if c['name'] == 'envoy-proxy')
                proxy['args'].extend(extra)
                path = Path(self.directory.name) / 'bootstrap-override.yaml'
                path.write_text(yaml.safe_dump_all(resources))
                result = self.validate('sim', path)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('bootstrap override', result.stderr)

    def test_stale_render_is_rejected_before_schema_validation(self):
        path = Path(self.directory.name) / 'stale.yaml'
        path.write_text(self.inputs['sim'].read_text() + '\n# old or edited output\n')
        result = self.validate('sim', path, policy_only=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('stale or modified rendered input', result.stderr)

    def test_fresh_render_without_required_pool_schema_fails(self):
        result = subprocess.run([
            sys.executable, '-B', str(ROOT / 'scripts/validate-llmd.py'), '--candidate', 'real',
            '--rendered', str(self.inputs['real']), '--chart', self.chart,
            '--crds', str(Path(self.directory.name) / 'absent-crds.yaml')], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing pinned GAIE CRD input', result.stderr)

    def test_synthetic_deployments_cannot_select_each_other(self):
        resources = list(yaml.safe_load_all(self.inputs['sim'].read_text()))
        backend = next(r for r in resources if r['metadata']['name'] == 'synthetic-backend-a')
        backend['spec']['selector']['matchLabels'] = {'app.kubernetes.io/name': 'llmd-inference-sim'}
        path = Path(self.directory.name) / 'overlap.yaml'
        path.write_text(yaml.safe_dump_all(resources))
        result = self.validate('sim', path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('backend selector', result.stderr)

    def test_route_cannot_disable_scheduler(self):
        resources = list(yaml.safe_load_all(self.inputs['sim'].read_text()))
        config = next(r for r in resources if 'envoy.yaml' in r.get('data', {}))
        bootstrap = yaml.safe_load(config['data']['envoy.yaml'])
        listener = next(l for l in bootstrap['static_resources']['listeners']
                        if l['address']['socket_address']['port_value'] == 8081)
        manager = listener['filter_chains'][0]['filters'][0]['typed_config']
        route = manager['route_config']['virtual_hosts'][0]['routes'][0]
        route['typed_per_filter_config']['envoy.filters.http.ext_proc'] = {'disabled': True}
        config['data']['envoy.yaml'] = yaml.safe_dump(bootstrap)
        path = Path(self.directory.name) / 'disabled-scheduler.yaml'
        path.write_text(yaml.safe_dump_all(resources))
        result = self.validate('sim', path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('scheduler override', result.stderr)

    def test_isolation_private_access_and_read_only_discovery_controls(self):
        for control in ('gpu', 'pvc', 'namespace', 'discovery-selector', 'public-service', 'rbac-write', 'model-download'):
            with self.subTest(control=control):
                resources = list(yaml.safe_load_all(self.inputs['sim'].read_text()))
                backend = next(r for r in resources if r['metadata']['name'] == 'synthetic-backend-a')
                router = next(r for r in resources if r['kind'] == 'Deployment' and r['metadata']['name'] == 'llmd-sim-epp')
                if control == 'gpu':
                    backend['spec']['template']['spec']['containers'][0]['resources']['limits']['nvidia.com/gpu'] = 1
                elif control == 'pvc':
                    backend['spec']['template']['spec']['volumes'] = [{'name': 'models', 'persistentVolumeClaim': {'claimName': 'vllm-models'}}]
                elif control == 'namespace':
                    backend['metadata']['namespace'] = 'inference'
                elif control == 'discovery-selector':
                    epp = next(c for c in router['spec']['template']['spec']['containers'] if c['name'] == 'epp')
                    epp['args'][epp['args'].index('--endpoint-selector') + 1] = 'app.kubernetes.io/name=vllm'
                elif control == 'public-service':
                    next(r for r in resources if r['kind'] == 'Service')['spec']['type'] = 'NodePort'
                elif control == 'model-download':
                    backend['spec']['template']['spec']['containers'][0]['args'].append('--tokenizer=Qwen/Qwen3-1.7B')
                else:
                    next(r for r in resources if r['kind'] == 'Role')['rules'][0]['verbs'].append('create')
                path = Path(self.directory.name) / f'{control}.yaml'
                path.write_text(yaml.safe_dump_all(resources))
                result = self.validate('sim', path)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn('validation failed:', result.stderr)
