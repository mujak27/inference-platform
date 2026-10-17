# Install a Linux GPU host: Ubuntu Desktop path

This guide prepares an Intel/AMD PC for later inference deployment. It does not
install Kubernetes or assume a particular disk, network, or user account. Ubuntu
Server is optional, not mandatory. Use local console access throughout installation.

Selected baseline: **Ubuntu Desktop 26.04 LTS, amd64**; see the
[decision record](adr/0001-ubuntu-desktop-26-04.md). The previously verified USB
contains **24.04**, not 26.04. To follow this baseline, obtain and verify the
26.04 ISO and recreate the installer; the older checksum does not apply.

**Never run flashing or partitioning commands against a guessed disk.** This
repository supplies no unattended disk-writing script. Stop whenever the target
or consequences are unclear.

## 1. Prepare and back up

1. Identify CPU architecture, motherboard model, disks (model/capacity), available
   space, GPU, and Ethernet/Wi-Fi adapter. Confirm the PC is x86-64 before choosing amd64.
2. Back up important files to a separate device and verify that you can read them.
3. If another OS exists, retain recovery media and encryption recovery keys
   outside this repository. Windows BitLocker/device encryption can require a
   recovery key after firmware or boot changes.
4. Decide which storage Linux may use. Reserve capacity for OS updates, container
   layers, weights, model downloads, and future experiment artifacts. The OS's
   minimum install size is not an inference storage budget.
5. Prepare an expendable USB stick, at least 8 GB and large enough for the chosen
   ISO; 16 GB or larger is a convenient choice. Back it up: flashing erases it.
6. Prefer wired Ethernet for the initial setup. Have a keyboard and display available.

### Disk layout is an owner decision

Dedicated Linux disk, shared-disk dual boot, and an existing Linux installation
are all possible inputs to this project. There is no platform-specific partition map.

For dual boot, follow Canonical's alongside-installation guidance linked below.
Back up Windows, retain its recovery key, disable Windows Fast Startup, and fully
shut it down before installation. If space must be reclaimed from Windows,
prepare it using Windows disk-management tools rather than guessing in Linux.
If the installer reports BitLocker or Intel RST, **stop** and follow the matching
Canonical guide; do not blindly disable encryption, change storage-controller
mode, delete partitions, or select “Erase disk” to bypass a warning.

The installation must preserve every partition outside the owner's approved
target. Validate that both operating systems still boot afterward if using dual boot.

## 2. Download and verify installation media (management computer)

1. Open the [official Ubuntu 26.04 release directory](https://releases.ubuntu.com/26.04/).
   Select an Ubuntu **Desktop 26.04 LTS amd64** ISO, not Server or ARM64. The ISO
   architecture follows the target PC, even when downloading on an Apple Silicon Mac.
2. Download the ISO, `SHA256SUMS`, and `SHA256SUMS.gpg` from that same release
   directory into a download folder outside Git. Record the exact ISO filename.
3. Follow [Canonical's signature-verification procedure](https://ubuntu.com/tutorials/how-to-verify-ubuntu).
   On macOS, GnuPG is available through `brew install gnupg` if Homebrew is already
   installed. Verify the signing key's full fingerprint against Canonical's guide,
   then authenticate the checksum file:

   ```sh
   gpg --keyid-format long --verify SHA256SUMS.gpg SHA256SUMS
   ```

   A “Good signature” is meaningful only with the expected signing key. Stop on
   a bad signature, missing key verification, or checksum mismatch.
4. On macOS, calculate the ISO digest with `shasum -a 256` followed by the actual
   quoted ISO path. Compare all 64 hex characters with that filename's entry in
   the authenticated `SHA256SUMS`. On Linux, use `sha256sum` instead.
5. Record filename, SHA-256, signing-key fingerprint, source URL, and verification
   date in your installation evidence. Updating packages after installation is
   still necessary; a recorded ISO does not freeze the eventual host packages.

Do not choose “latest” blindly: the primary download page may offer a newer LTS
than this guide's 26.04 LTS baseline. Exact media selection and verification are a
manual gate; no installation image was downloaded or verified by the agent.

## 3. Flash the USB (macOS path)

This writes the **USB installer**, not the PC's internal disk.

1. Download [balenaEtcher](https://etcher.balena.io/) from its official site.
   Select the macOS build matching your Mac (arm64 for Apple Silicon).
2. Disconnect unnecessary external disks to reduce target-selection mistakes.
3. Insert the expendable USB and open Etcher.
4. Choose **Flash from file** and select the verified Ubuntu amd64 ISO.
5. Choose **Select target**. Match the USB's model and capacity. Do not select
   the Mac's internal disk or a backup disk.
6. **Destructive checkpoint:** explicitly confirm that this USB may be erased.
7. Choose **Flash!**, approve macOS authorization if requested, and wait for both
   writing and validation to finish. Stop if validation fails.
8. Eject the USB. If macOS offers to initialize an unreadable disk, choose
   **Ignore**, not Initialize; the Linux installer need not be mountable by macOS.

For Linux/Windows clients, Canonical documents Disks and Rufus in its
[USB creation guide](https://documentation.ubuntu.com/desktop/en/latest/how-to/create-a-bootable-usb-stick/).

## 4. Boot and try Ubuntu (target PC)

1. Fully shut down the PC and insert the USB.
2. Use the motherboard's one-time boot menu; check its manual for the correct
   key. Choose the USB's UEFI entry on a UEFI system. Do not change boot mode
   or storage-controller settings speculatively.
3. Keep Secure Boot enabled initially. Ubuntu supports signed NVIDIA drivers;
   enrollment steps may be required later. Do not disable it as a default fix.
4. Choose **Try Ubuntu** before installation. Check display, keyboard, network,
   and storage visibility. A live session is not proof of CUDA or inference support.
5. If the installer cannot see the expected disks/network, stop and troubleshoot
   that hardware rather than continuing with an unexpected target.

## 5. Install Ubuntu Desktop (target PC)

1. Start **Install Ubuntu**. Choose language, keyboard, timezone, and network.
2. Choose interactive installation and the default application selection; extra
   office applications are not needed for serving.
3. Enable third-party graphics/Wi-Fi drivers if offered. If prompted to create a
   Secure Boot enrollment password, retain it privately for the next reboot.
4. At disk setup, use only the owner's approved storage plan. If preserving an
   OS, do not use whole-disk erase on its disk. Use the alongside option only
   when available and its proposed changes match that plan; otherwise stop for
   disk-specific guidance. Manual partitioning is not a universal safe fallback.
5. Create a normal administrative user with a strong password and a chosen
   hostname. Do not put passwords in installation notes or Git.
6. Choose encryption deliberately. Passphrase-unlocked disks may require a
   person at the console after reboot, which affects remote recovery.
7. **Destructive checkpoint:** review the final disk/partition summary against
   backups and the approved target before clicking Install. If anything differs, cancel.
8. Complete installation, restart, and remove the USB when prompted. Complete
   any Secure Boot MOK enrollment requested by the driver installation using
   the password you created; retain console access until the driver works.
9. Verify Ubuntu starts from internal storage and that any preserved OS still boots.

Installer labels/screens vary by release. Canonical's current
[installation tutorial](https://documentation.ubuntu.com/desktop/en/latest/tutorial/install-ubuntu-desktop/)
may show a newer Ubuntu release; use it for explanation, not to override the
selected version or disk-safety checkpoints.

## 6. Handoff to host bootstrap

Continue with [bootstrap.md](bootstrap.md): updates, private SSH, suspend settings,
NVIDIA driver inspection, and inventory. Do not expose SSH through the router or
install several cluster distributions “to try them” on the same host.

Installation acceptance: Ubuntu boots, intended data/OS are preserved, local
network works, media identity is recorded, and console access is retained.
CUDA/container/Kubernetes acceptance remains pending.
