#!/usr/bin/env python3
"""Offline source checks, not EPP/Envoy binary acceptance or runtime qualification."""
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
EPP = 'ghcr.io/llm-d/llm-d-router-endpoint-picker:v0.11.0@sha256:39257d24552d16d8f215d3de25cc734fd44af3b282b67032db01aff900c610cf'
ENVOY = 'docker.io/envoyproxy/envoy:distroless-v1.37.8@sha256:036ffe3333bd35828fd229d79cb5f2216082bd8a9732cff69db0413d96ae0150'
SIM = 'ghcr.io/llm-d/llm-d-inference-sim:v0.11.2@sha256:32144df791330a0006b747edfdf2b114a0fe728e023a9d1b3463eeb48d32abb9'
SYNTHETIC = {'app.kubernetes.io/name': 'llmd-inference-sim', 'inference.platform/experiment': 'synthetic-only'}
CRD_SHA256 = 'cd7cc63149943627f92d401991886a631d938de28edb416312c443a1b7f42ded'
BUILTIN_SCHEMAS = 'https://raw.githubusercontent.com/yannh/kubernetes-json-schema/aff1ca44984cbbcfa376c1cb6fdc4bb6aa0381fd/{{.NormalizedKubernetesVersion}}-standalone{{.StrictSuffix}}/{{.ResourceKind}}{{.KindSuffix}}.json'


class UniqueLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        keys = [self.construct_object(key, deep=deep) for key, _ in node.value]
        if len(keys) != len(set(keys)):
            raise ValueError('duplicate YAML key')
        return super().construct_mapping(node, deep=deep)


def documents(text):
    result = [r for r in yaml.load_all(text, Loader=UniqueLoader) if r is not None]
    require(bool(result) and all(isinstance(r, dict) for r in result), 'empty or invalid documents')
    return result


def require(condition, message):
    if not condition:
        raise ValueError(message)


def mounted_config(resources, pod, container, path):
    mount, = [m for m in container['volumeMounts'] if str(Path(path).parent) == m['mountPath']]
    require(not mount.get('subPath'), 'unexpected config subPath')
    volume, = [v for v in pod['volumes'] if v['name'] == mount['name']]
    reference = volume['configMap']
    config, = [r for r in resources if r['kind'] == 'ConfigMap' and r['metadata']['name'] == reference['name']]
    filename = Path(path).name
    keys = [i['key'] for i in reference.get('items', [{'key': filename, 'path': filename}]) if i['path'] == filename]
    key, = keys
    body, = documents(config['data'][key])
    return body


def policy(resources, candidate):
    synthetic = candidate == 'sim'
    namespace = 'llmd-sim' if synthetic else 'inference'
    router_name = 'llmd-sim-epp' if synthetic else 'llmd-epp'
    selector = SYNTHETIC if synthetic else {'app.kubernetes.io/name': 'vllm'}
    allowed = {'Deployment', 'Service', 'ConfigMap', 'ServiceAccount', 'Role', 'RoleBinding'}
    allowed.add('Namespace' if synthetic else 'InferencePool')
    identities = set()
    for r in resources:
        kind, meta = r['kind'], r['metadata']
        require(kind in allowed, 'unexpected resource kind')
        require(meta['name'] == namespace if kind == 'Namespace' else meta.get('namespace') == namespace,
                'candidate namespace isolation violated')
        identity = (r['apiVersion'], kind, meta['name'])
        require(identity not in identities, 'duplicate resource')
        identities.add(identity)
        if kind == 'ConfigMap':
            for key, text in r.get('data', {}).items():
                if key.endswith('.yaml'):
                    documents(text)
    deployments = [r for r in resources if r['kind'] == 'Deployment']
    require(len(deployments) == (3 if synthetic else 1), 'unexpected deployment count')
    router, = [r for r in deployments if r['metadata']['name'] == router_name]
    for deployment in deployments:
        spec = deployment['spec']
        require(spec['replicas'] == 1 and spec['strategy'] == {'type': 'Recreate'}, 'unsafe rollout')
        labels = spec['template']['metadata']['labels']
        require(all(labels.get(k) == v for k, v in spec['selector']['matchLabels'].items()), 'deployment selector mismatch')
        pod = spec['template']['spec']
        for key in ('hostNetwork', 'hostPID', 'hostIPC', 'initContainers', 'ephemeralContainers', 'resourceClaims'):
            require(not pod.get(key), 'host/GPU isolation violated')
        for volume in pod.get('volumes', []):
            require(set(volume) - {'name'} == {'configMap'}, 'GPU/PVC/model volume forbidden')
        for c in pod['containers']:
            require(c['image'] in ({EPP, ENVOY} if deployment is router else {SIM}), 'unexpected image')
            require(not c.get('securityContext', {}).get('privileged'), 'privileged container forbidden')
            require(not any('hostPort' in p for p in c.get('ports', [])), 'private endpoint violation')
            for values in c.get('resources', {}).values():
                require(set(values) <= {'cpu', 'memory'}, 'GPU/extended resources forbidden')
        if deployment is not router:
            require(all(labels.get(k) == v for k, v in SYNTHETIC.items()), 'synthetic selector isolation violated')
            matches = [other for other in deployments if all(
                other['spec']['template']['metadata']['labels'].get(k) == v
                for k, v in spec['selector']['matchLabels'].items())]
            require(matches == [deployment], 'backend selector overlaps another deployment')
            require(pod.get('automountServiceAccountToken') is False and not pod.get('volumes'), 'backend API/model access forbidden')
            require(len(pod['containers']) == 1, 'unexpected backend container')
            c = pod['containers'][0]
            require(c['args'] == [
                '--model=synthetic-llmd-sim-only', '--mode=echo', '--port=8000', '--max-num-seqs=2',
                '--max-waiting-queue-length=16', '--max-model-len=1024', '--latency-calculator=constant',
                '--time-to-first-token=100ms', '--inter-token-latency=20ms', '--enable-request-id-headers',
                '--fake-metrics={"running-requests":0,"waiting-requests":0,"kv-cache-usage":0}'],
                'synthetic backend arguments must not enable model/tokenizer acquisition')
            require(c['securityContext'] == {
                'runAsNonRoot': True, 'allowPrivilegeEscalation': False, 'readOnlyRootFilesystem': True,
                'capabilities': {'drop': ['ALL']}, 'seccompProfile': {'type': 'RuntimeDefault'}},
                'synthetic backend security profile changed')
    pod = router['spec']['template']['spec']
    require(pod.get('serviceAccountName') == router_name and pod.get('automountServiceAccountToken') is not False,
            'router discovery identity missing')
    require(len(pod['containers']) == 2, 'unexpected router containers')
    epp, = [c for c in pod['containers'] if c['name'] == 'epp']
    proxy, = [c for c in pod['containers'] if c['name'] == 'envoy-proxy']
    require(epp['image'] == EPP and proxy['image'] == ENVOY, 'router image mismatch')
    config = mounted_config(resources, pod, epp, epp['args'][epp['args'].index('--config-file') + 1])
    require(config['apiVersion'] == 'llm-d.ai/v1alpha1' and config['kind'] == 'EndpointPickerConfig', 'invalid EPP config identity')
    if synthetic:
        args = epp['args']
        require(dict(p.split('=', 1) for p in args[args.index('--endpoint-selector') + 1].split(',')) == selector,
                'synthetic selector isolation violated')
        require(args[args.index('--endpoint-target-ports') + 1] == '8000' and not any(a.startswith('--pool-') for a in args), 'unexpected synthetic discovery')
        expected = yaml.safe_load((ROOT / 'apps/llmd/simulator/router-values.yaml').read_text())['router']['epp']['pluginsConfig']
        require(config == expected, 'synthetic profile mismatch')
    else:
        pool, = [r for r in resources if r['kind'] == 'InferencePool']
        require(pool['apiVersion'] == 'inference.networking.k8s.io/v1', 'wrong pool API')
        spec = pool['spec']
        require(spec['selector']['matchLabels'] == selector and spec['targetPorts'] == [{'number': 8000}], 'real selector/port isolation violated')
        require(spec['endpointPickerRef'] == {'name': router_name, 'port': {'number': 9002}, 'failureMode': 'FailClose'}, 'pool must be fail-closed')
        args = epp['args']
        require(args[args.index('--pool-name') + 1] == pool['metadata']['name'] and
                args[args.index('--pool-namespace') + 1] == namespace and
                args[args.index('--pool-group') + 1] == 'inference.networking.k8s.io', 'pool discovery mismatch')
    proxy_args = proxy['args']
    require(proxy_args.count('-c') == 1 and not any(
        arg.split('=', 1)[0] in ('--config-yaml', '--config-path') or
        (arg.startswith('-c') and arg != '-c') for arg in proxy_args),
        'Envoy bootstrap override arguments are forbidden')
    bootstrap = mounted_config(resources, pod, proxy, proxy_args[proxy_args.index('-c') + 1])
    listeners = [l for l in bootstrap['static_resources']['listeners'] if l['address']['socket_address']['port_value'] == 8081]
    listener, = listeners
    managers = [f['typed_config'] for chain in listener['filter_chains'] for f in chain['filters']
                if f['name'] == 'envoy.filters.network.http_connection_manager']
    manager, = managers
    filters = [f['typed_config'] for f in manager['http_filters'] if f['name'] == 'envoy.filters.http.ext_proc']
    ext_proc, = filters
    require(ext_proc.get('failure_mode_allow') is False, 'request-path ext_proc must be fail-closed')
    require(ext_proc['grpc_service']['envoy_grpc']['cluster_name'] == 'ext_proc', 'unexpected scheduler target')
    route_config = manager['route_config']
    for host in route_config['virtual_hosts']:
        for scope in [route_config, host] + host['routes']:
            override = scope.get('typed_per_filter_config', {}).get('envoy.filters.http.ext_proc')
            require(override is None or override == {
                '@type': 'type.googleapis.com/envoy.config.route.v3.FilterConfig', 'config': {}},
                'scheduler override must not disable or relax fail-closed processing')
    admin = bootstrap['admin']['address']['socket_address']
    require(admin['address'] == '127.0.0.1', 'Envoy admin must be loopback-only')
    services = [r for r in resources if r['kind'] == 'Service']
    require(len(services) == 1, 'unexpected service count')
    for service in services:
        spec = service['spec']
        require(spec.get('type', 'ClusterIP') == 'ClusterIP' and not spec.get('externalIPs') and not spec.get('loadBalancerIP'), 'private endpoint violation')
        require(any(p['port'] == 80 and p.get('targetPort') == 8081 for p in spec['ports']), 'proxy service port missing')
        for deployment in deployments:
            labels = deployment['spec']['template']['metadata']['labels']
            matches = all(labels.get(k) == v for k, v in spec['selector'].items())
            require(matches == (deployment is router), 'service selects unintended backend')
    rules = [(tuple(rule['apiGroups']), tuple(rule['resources']), frozenset(rule['verbs']))
             for r in resources if r['kind'] == 'Role' for rule in r['rules']]
    expected_rules = [(('',), ('pods',), frozenset(('get', 'list', 'watch')))]
    if not synthetic:
        expected_rules.append((('inference.networking.k8s.io',), ('inferencepools',), frozenset(('get', 'list', 'watch'))))
    require(len(rules) == len(expected_rules) and set(rules) == set(expected_rules), 'discovery RBAC exceeds required reads')
    roles = [r for r in resources if r['kind'] == 'Role']
    require(len(roles) == 1, 'unexpected discovery roles')
    binding, = [r for r in resources if r['kind'] == 'RoleBinding']
    require(binding['roleRef'] == {'apiGroup': 'rbac.authorization.k8s.io', 'kind': 'Role', 'name': roles[0]['metadata']['name']} and
            binding['subjects'] == [{'kind': 'ServiceAccount', 'name': router_name, 'namespace': namespace}], 'discovery RBAC identity mismatch')
    for path in ('apps/kustomization.yaml', 'infra/kustomization.yaml'):
        require('llmd' not in (ROOT / path).read_text(), 'candidate must remain unregistered')


def strict_schema(value):
    # This pinned pool schema has no nullable/int-or-string fields or references.
    # CEL and full ObjectMeta admission remain API-server gates, not JSON Schema proof.
    if isinstance(value, dict):
        if 'properties' in value:
            value.setdefault('additionalProperties', False)
        for child in value.values():
            strict_schema(child)
    elif isinstance(value, list):
        for child in value:
            strict_schema(child)


def schemas(resources, candidate, crds):
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        tool = os.environ.get('KUBECONFORM', 'kubeconform')
        if candidate == 'real':
            require(crds.is_file(), 'missing pinned GAIE CRD input; acquire v1.5.0 v1-manifests.yaml separately')
            require(hashlib.sha256(crds.read_bytes()).hexdigest() == CRD_SHA256, 'GAIE CRD checksum mismatch')
            crd, = [r for r in documents(crds.read_text()) if r['spec']['group'] == 'inference.networking.k8s.io'
                    and r['spec']['names']['kind'] == 'InferencePool']
            version, = [v for v in crd['spec']['versions'] if v['name'] == 'v1' and v['served']]
            schema = version['schema']['openAPIV3Schema']
            strict_schema(schema)
            (directory / 'inferencepool.json').write_text(json.dumps(schema))
            pool, = [r for r in resources if r['kind'] == 'InferencePool']
            path = directory / 'pool.yaml'
            path.write_text(yaml.safe_dump(pool))
            command = [tool, '-strict', '-summary', '-schema-location', str(directory / '{{.ResourceKind}}.json')]
            subprocess.run(command + [str(path)], check=True, timeout=60)
            for name, mutate in (
                ('failure-mode', lambda p: p['spec']['endpointPickerRef'].update(failureMode='FailClosed')),
                ('port', lambda p: p['spec']['targetPorts'][0].update(number=65536)),
                ('unknown-field', lambda p: p['spec'].update(notAField=True)),
            ):
                bad = copy.deepcopy(pool)
                mutate(bad)
                negative = directory / f'invalid-{name}.yaml'
                negative.write_text(yaml.safe_dump(bad))
                result = subprocess.run(command + [str(negative)], text=True, capture_output=True, timeout=60)
                require(result.returncode != 0 and 'is invalid' in result.stdout,
                        f'schema negative control did not explicitly reject {name}: {result.stdout}{result.stderr}')
        builtins = directory / 'builtins.yaml'
        builtins.write_text(yaml.safe_dump_all([r for r in resources if r['kind'] != 'InferencePool']))
        command = [tool, '-strict', '-summary', '-kubernetes-version', '1.35.0',
                   '-schema-location', BUILTIN_SCHEMAS]
        subprocess.run(command + [str(builtins)], check=True, timeout=120)
        bad = copy.deepcopy(next(r for r in resources if r['kind'] == 'Deployment'))
        bad['spec']['deliberatelyUnknown'] = True
        negative = directory / 'invalid-deployment.yaml'
        negative.write_text(yaml.safe_dump(bad))
        result = subprocess.run(command + [str(negative)], text=True, capture_output=True, timeout=120)
        require(result.returncode != 0 and 'is invalid' in result.stdout,
                f'built-in schema negative control was not explicitly rejected: {result.stdout}{result.stderr}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', choices=('real', 'sim'), required=True)
    parser.add_argument('--rendered', type=Path)
    parser.add_argument('--chart', type=Path, default=ROOT / '.local/llmd/llm-d-router-standalone-v0.11.0.tgz')
    parser.add_argument('--crds', type=Path, default=ROOT / '.local/llmd/crds.yaml')
    parser.add_argument('--policy-only', action='store_true', help='inspect supplied YAML only; no freshness/schema proof (not the CI gate)')
    args = parser.parse_args()
    rendered = args.rendered or ROOT / ('.local/llmd/rendered.yaml' if args.candidate == 'real' else '.local/llmd-sim/rendered.yaml')
    if not rendered.is_file():
        parser.error(f'missing rendered input: {rendered}; run the offline render command')
    try:
        resources = documents(rendered.read_text())
        policy(resources, args.candidate)
        if not args.policy_only:
            with tempfile.TemporaryDirectory() as directory:
                fresh = Path(directory) / 'fresh.yaml'
                subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/render-llmd.py'),
                                '--candidate', args.candidate, '--chart', str(args.chart),
                                '--output', str(fresh)], check=True, timeout=150)
                require(fresh.read_bytes() == rendered.read_bytes(), 'stale or modified rendered input; rerender from current sources')
            schemas(resources, args.candidate, args.crds)
            print('SOURCE CHECKS: current render, source policy and JSON schemas passed')
        else:
            print('POLICY ONLY: supplied YAML passes source policy; freshness/schema not checked')
        print('PENDING: pinned EPP/Envoy binary acceptance, admission, amd64 and runtime gates')
    except (OSError, ValueError, KeyError, TypeError, IndexError, yaml.YAMLError, subprocess.SubprocessError) as error:
        parser.exit(1, f'validation failed: {error}\n')


if __name__ == '__main__':
    main()
