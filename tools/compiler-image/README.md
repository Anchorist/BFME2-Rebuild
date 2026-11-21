# Isolated compiler image build scripts

These scripts build and verify the Ubuntu 24.04 (`noble`) + Wine 9.0 + Visual C++ 7.1
compiler runtime used by the hosted **BFME II / Boat** checks (`bfme2-compiler-v1`), and
compile single translation units through the same `/usr/local/libexec/bfme2-compiler/run`
entry point.

See [docs/compiler-image.md](../../docs/compiler-image.md) for the complete specification,
required user-supplied inputs and SHA-256 digests, directory layout, exact compile
contract, verification steps, and publication notes.

## Files

- `build.sh` — end-to-end builder (`fresh-install.sh`, `outer-wine.sh`, `seal.sh seal`, `control.sh --install`) given `--inputs DIR`.
- `fresh-install.sh` — installs host prerequisites, creates `ci-compile`, builds the minimal Ubuntu 24.04 + Wine `9.0~repack-4build3` rootfs and Wine prefix, installs user inputs under `/opt/boat-compiler/tools/`, installs `guard/`, and writes initial manifests.
- `outer-wine.sh` — installs matching host `wine=9.0~repack-4build3` and `wine64=9.0~repack-4build3`.
- `root-probe-access.sh` — grants `ci-compile` traverse-only (`--x`) ACL on `/root` so the probe can confirm `ENOENT` on `/root/.ssh` without reading `/root`.
- `seal.sh` — seals or verifies `input.sha256`, `runtime-files.sha256`, `runtime-links.tsv`, `runtime-packages.tsv`, `image-inventory.json`, `worker.json`, and the unprivileged isolation probe.
- `run` — installed at `/usr/local/libexec/bfme2-compiler/run`; drops to `ci-compile` with a scrubbed environment for `probe` and `compile`.
- `managed_probe.py` — installed at `/usr/local/libexec/bfme2-compiler/managed_probe.py`; audits the sealed profile and inner `bwrap` isolation boundary.
- `control.sh` — verifies `/usr/local/libexec/bfme2-compiler/run` with synthetic supervisor tokens, a one-file compile control, and deliberate `C2065` and `C1189` error controls.
- `compile_one.sh` / `compile_one.py` — compiles one translation unit from a checkout using the exact check flags and environment and prints the COFF object SHA-256 and timestamp-normalized COFF SHA-256.
- `worker-template.json` — profile template populated during installation.
- `wine_socket_direct.c` — small i386 `ld.so.preload` shim routing Ubuntu 24.04 i386 glibc socket wrappers to direct Linux socket syscalls so `pool_network.py` can inspect `AF_UNIX` while blocking `socketcall(102)`.
- `guard/` — isolated runtime modules installed under `/opt/boat-compiler/guard/` (`pool_bootstrap.sh`, `pool_compiler.py`, `pool_launcher.py`, `pool_network.py`, `pool_probe.py`, `pool_protocol.py`, `pool_worker.py`).
