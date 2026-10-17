# Use Ubuntu Desktop 26.04 LTS for the reference host

Accepted 2026-10-17. The owner chose Ubuntu 26 instead of the initially proposed
24.04 baseline; this project interprets that as **Ubuntu Desktop 26.04 LTS,
amd64**, not the interim 26.10 release. This replaces the 24.04 recommendation,
while retaining Desktop as the graphical installation path rather than requiring Server.

The platform continues to depend on validated Linux GPU/runtime capabilities,
not a desktop environment or a particular partition layout. NVIDIA Container
Toolkit's reviewed platform table lists 26.04, but the complete driver,
Kubernetes, and inference runtime combination still requires hardware validation.

The verified 24.04 ISO/USB result remains historical evidence only. Download,
signature/checksum verification, and USB read-back must be repeated for 26.04;
no 26.04 installation or inference support is claimed verified by this decision.
