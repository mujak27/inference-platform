# Host bootstrap and private access

Run host commands **on the installed Ubuntu machine**, not on the management Mac.
These are explicit manual steps, not commands the agent has executed remotely.
Keep local console access until SSH and the NVIDIA driver survive a reboot.

## 1. Update the host

```sh
sudo apt update
sudo apt upgrade
sudo apt install openssh-server ubuntu-drivers-common pciutils mokutil git
sudo systemctl enable --now ssh
```

Review package changes before confirming. Reboot after kernel/driver updates at
a time you approve. Do not turn off security updates to keep version numbers fixed;
record changes and repeat GPU validation after upgrades.

## 2. Establish a private network path

1. Connect the management client and GPU host to a trusted LAN (prefer Ethernet).
   For separate networks, arrange an authenticated VPN rather than public port forwarding.
2. On Ubuntu, inspect addresses using `ip -br address` and routing with `ip route`.
   Use the LAN address, not loopback or a container bridge. Reserve a stable DHCP
   lease in the router if you administer it; no IP is hard-coded in this project.
3. On Ubuntu, inspect the SSH host-key fingerprint:

   ```sh
   sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
   ```

4. At the management client, connect with `ssh` using the chosen Ubuntu username
   and LAN address. Compare the first-connection fingerprint with the console
   value before trusting it. Never disable host-key checking to bypass a mismatch.
5. Use an existing SSH key or generate a dedicated passphrase-protected Ed25519
   key with `ssh-keygen`. Keep the private key on the client. Append only its
   `.pub` contents to the Ubuntu user's `~/.ssh/authorized_keys`; set directory
   mode 700 and file mode 600. Do not overwrite other authorized keys.
6. Test key-based access in a **second** client terminal. Keep the first session
   and console available until that succeeds.

An optional client-only `~/.ssh/config` alias can hold the actual host, username,
and identity path. Do not commit personal network settings or keys to this repo.

### Firewall and SSH hardening

On the Ubuntu console, inspect `sudo ufw status verbose`. If no other firewall
policy exists and you choose UFW, allow TCP 22 **from your actual management IP
or trusted subnet**, then enable UFW. Use `sudo ufw allow from` followed by the
actual source address and `to any port 22 proto tcp`. Review the rule before
enabling. Do not copy a sample subnet or open SSH to all sources by default.

Confirm a second SSH session succeeds after firewall changes. Do not disable an
existing firewall. Later Kubernetes CNI/API traffic needs a separate reviewed
firewall policy; an SSH-only host rule set is not a complete cluster policy.

After key access works, review effective SSH settings with `sudo sshd -T`.
If disabling password authentication, use Ubuntu's documented configuration
mechanism, account for both password and keyboard-interactive authentication,
run `sudo sshd -t`, then reload `ssh`. Verify effective settings and a new login
before closing existing access. Never automate this before validating keys.

## 3. Keep the desktop available

In Ubuntu Desktop **Settings → Power**, turn off automatic suspend while serving
on mains power. Screen blanking/locking can stay enabled. Verify that SSH remains
available after the machine sits idle. Do not globally mask sleep targets unless
there is a demonstrated need. A reboot into another OS intentionally takes the
platform offline.

Record idle GPU memory, avoid games/browsers/other GPU workloads during benchmarks,
and do not assume the full VRAM capacity is free just because no inference runs.

## 4. Validate/install the NVIDIA driver

First inspect rather than install another driver over a working one:

```sh
lspci -nn
ubuntu-drivers devices
ubuntu-drivers list
mokutil --sb-state
nvidia-smi
```

If `nvidia-smi` already succeeds, record the driver and GPU; a reinstall is not
required. If no working NVIDIA driver exists, use the Ubuntu-supported selection
path for this desktop:

```sh
sudo ubuntu-drivers install
```

Review its selected branch and packages, then reboot at the console and complete
any required Secure Boot enrollment. Run `nvidia-smi` again and record versions
with `cat /proc/driver/nvidia/version` and `uname -r`.

The recommended driver is discovered from the actual hardware/repositories; this
guide does not invent a tested branch. Before deploying a CUDA image, compare
its required driver version with the installed driver. Do not mix Ubuntu package
drivers with NVIDIA `.run` installers or install host CUDA toolkits blindly.
The “CUDA Version” printed by `nvidia-smi` indicates driver capability, **not** an
installed toolkit version or successful CUDA computation.

On failure, retain the error and inspect Secure Boot state, enrollment, loaded
modules, and kernel logs using Canonical's driver guide. Do not repeatedly swap
drivers or disable Secure Boot without identifying the cause.

## 5. Collect host inventory

Transfer this repository to the host over the private connection (or clone it
once a remote exists). From its root on Ubuntu:

```sh
mkdir -p .local/evidence
bash scripts/preflight.sh > .local/evidence/host-preflight.txt 2>&1
status=$?
cat .local/evidence/host-preflight.txt
printf 'Preflight exit status: %s\n' "$status"
```

The script is read-only, needs no sudo, and does not contact a cluster. Exit 0
means its **host inventory/driver checks** passed, not that milestone 0 passed.
Exit 1 indicates a failed host check, and exit 2 indicates usage error. It does
not perform CUDA computation, container validation, or GPU allocation in Kubernetes.

Keep raw output private: it may contain device/network identifiers. Commit only
reviewed, redacted evidence and exact version records. Update [versions.md](versions.md)
and [milestones.md](milestones.md) with observed facts, dates, and evidence paths.

## 6. Stop gate: select the runtime and cluster next

Before installing container software or Kubernetes, review the host inventory,
driver compatibility, storage, swap policy, and private network path. Select one
lightweight distribution with a supported GPU runtime setup and pin it. Avoid
unnecessary Kubernetes-in-Docker nesting and duplicate runtime/device-plugin installs.

The next hardware slice must pin a CUDA compute-test image and dependencies, perform an
asserted GPU calculation inside it, then prove Kubernetes GPU allocation. Do not
treat `nvidia-smi` in a container as satisfying that gate. Only after those checks
should the prepared vLLM candidate be deployed. Its manifests can be rendered
without hardware; see [the GitOps guide](gitops.md). llm-d and LMCache wait for real serving.

## References checked 2026-10-17

- [Ubuntu OpenSSH](https://documentation.ubuntu.com/server/how-to/security/openssh-server/)
- [Ubuntu firewall](https://documentation.ubuntu.com/server/how-to/security/firewalls/)
- [Ubuntu NVIDIA drivers](https://documentation.ubuntu.com/server/how-to/graphics/install-nvidia-drivers/)
- [NVIDIA Container Toolkit installation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
