# Compiler Image (`bfme2-compiler-v1`)

This document describes the isolated compiler image used by the hosted **BFME II / Boat** pull-request checks and shows how to rebuild and verify an equivalent image yourself using the scripts in [`tools/compiler-image/`](../tools/compiler-image/).

## What the image is

The hosted compiler runner (`bfme2-compiler-v1`) is an Ubuntu 24.04 (`ubuntu-noble`) `x86_64` host containing a sealed, read-only compiler runtime under `/opt/boat-compiler` and a fixed local entry point at `/usr/local/libexec/bfme2-compiler/run`:

- **Base OS and container rootfs:** Ubuntu 24.04 (`noble`) `x86_64`, minimal `debootstrap` rootfs (`--variant=minbase --include=ca-certificates,python3,util-linux`) with `i386` enabled.
- **Wine:** Ubuntu 24.04 packages `wine`, `wine64`, and (inside the sealed rootfs) `wine32:i386`, `wine32-preloader:i386`, and `wine64-preloader`, all pinned to **`9.0~repack-4build3`**. Inside the sealed rootfs, `/etc/ld.so.preload` loads `/$LIB/wine-socket-direct.so` (built from [`tools/compiler-image/wine_socket_direct.c`](../tools/compiler-image/wine_socket_direct.c)) so Ubuntu 24.04 `i386` glibc uses direct Linux socket syscalls instead of legacy `socketcall(102)`, allowing the seccomp filter to inspect `AF_UNIX` directly while blocking `socketcall`.
- **Compiler:** Microsoft Visual C++ .NET 2003 (`cl.exe` file version `13.10.3077`, product version `7.10.3077`, x86) and its runtime DLLs (`msvcr71.dll`, `msvcp71.dll`, `mspdb71.dll`).
- **SDK headers:** Bundled Visual C++ 7.1 headers/libraries, Visual C++ 7.1 Platform SDK headers, and Microsoft DirectX SDK (August 2005) headers (`Include/`).
- **STLport:** Pristine STLport 4.5.3 (legacy opt-in) and pristine STLport 4.6 (`_STLPORT_VERSION 0x460`, official archive SHA-256 `744dd31ac34246bdba4ef50f79b4d936c842a3e4f13915a86cc06f7c7cf84f60`) plus the project's approved 4.6 overlay and allocator shim directories.
- **No game files or credentials:** Neither `baseline/game.dat`, nor any game assets, nor any repository credentials are present in the compiler image.

## User-supplied inputs

This repository does **not** ship proprietary Microsoft Visual C++ 7.1 binaries, runtime DLLs, Platform SDK headers, or DirectX SDK headers. To rebuild the image, place copies you are entitled to use—together with the STLport trees and overlays from the Open-BFME-2 toolchain support tree documented in [`tools/README.md`](../tools/README.md)—into a single inputs directory (`--inputs DIR`) with the following layout:

```text
<inputs>/
├── vc/
│   ├── Common7/IDE/
│   │   ├── mspdb71.dll
│   │   └── msvcr71.dll
│   └── Vc7/
│       ├── bin/
│       │   ├── c1.dll
│       │   ├── c1xx.dll
│       │   ├── c2.dll
│       │   └── cl.exe
│       ├── include/          (155 files)
│       ├── lib/              (45 files)
│       └── PlatformSDK/      (1,136 files; Include/ used during compile)
├── vcruntime/
│   ├── msvcp71.dll
│   └── msvcr71.dll
├── dx/
│   └── Include/              (62 files; August 2005 DirectX SDK, matching ci/managed-check/dxsdk-includes.manifest)
├── stlport/                  (STLport 4.5.3)
├── stlport-4.6/              (pristine STLport 4.6: stlport/, src/, README, PROVENANCE.md, SHA256SUMS)
├── overlay/
│   ├── base/
│   ├── bfmealloc/
│   ├── bfmealloc_alloconly/
│   ├── bfmehashtable/
│   └── bfmelist/
└── allocator/
    ├── README.md
    └── stl/_alloc.h
```

### Required proprietary binary SHA-256 digests

| Relative path under `/opt/boat-compiler/tools/` | SHA-256 |
| --- | --- |
| `tools/vc/Vc7/bin/cl.exe` | `2ecf86a3edfd3deae498e08298e210e984537ce9e11759930561e43f40bd2515` |
| `tools/vc/Vc7/bin/c1.dll` | `11f452af93f8e686b36b348763b33d32ae2766f1b0c360a447053bf44ec50fcc` |
| `tools/vc/Vc7/bin/c1xx.dll` | `353f3d5dcd050b876e1c044b99c4bf47958d255f395a4919f406a19921be4dfa` |
| `tools/vc/Vc7/bin/c2.dll` | `bcd28f39b1798b07989c30a1df471cf87fc20e3802d130901a08f83800e6b81e` |
| `tools/vc/Common7/IDE/mspdb71.dll` | `85ebd7dcbe1b9fa756f23e5f811d7dfeccdac0de14271f2c18affbf918d8cb79` |
| `tools/vc/Common7/IDE/msvcr71.dll` | `8094af5ee310714caebccaeee7769ffb08048503ba478b879edfef5f1a24fefe` |
| `tools/vcruntime/msvcp71.dll` | `df96156f6a548fd6fe5672918de5ae4509d3c810a57bffd2a91de45a3ed5b23b` |
| `tools/vcruntime/msvcr71.dll` | `8094af5ee310714caebccaeee7769ffb08048503ba478b879edfef5f1a24fefe` |

### Subtree manifest SHA-256 digests

Each subtree digest below is the SHA-256 of the `LC_ALL=C`-sorted `sha256sum` listing (`<sha256>  tools/<path>\n`) computed from `/opt/boat-compiler`:

| Subtree | File count | Listing SHA-256 |
| --- | ---: | --- |
| `tools/vc/Vc7/bin` | 4 | `c244eadfab0ff5f05b9f58ff791fd91f1504c643f5bcb090c739da5f40edcc47` |
| `tools/vc/Common7/IDE` | 2 | `b85e6430448c5b7e15b41a30c6c9f193da4e70179a775f4ec3c6142c7316f815` |
| `tools/vc/Vc7/include` | 155 | `d82a2603307a398644a23ad9dabb08b6f03ea8feb8f71e644a3ae71249209530` |
| `tools/vc/Vc7/lib` | 45 | `2f68a8866279dd648160168e134ceb465fd165c1765fb08a70b82e24428cb5b5` |
| `tools/vc/Vc7/PlatformSDK` | 1,136 | `d9ed34039994fb0edd9cd14ae97ae94595438a0786fccc415f7856886c11e349` |
| `tools/dx/Include` | 62 | `9d457a0c1e38fec5c872ab3fb8dcc6d1dfacdaa28954f73d3d4b9e16d09abb63` |
| `tools/stlport-4.6/stlport` | 414 | `0475b8fd2ed2d22eff5d66bf7a47148a920aff0ad3550fcb3d3df425d3886121` |
| `tools/stlport-4.6/src` | 116 | `2b36b6b526fb4b3e2a0df4e9fbd27c88b646afe9b1a80d5dec755b3a27641bf6` |
| `tools/overlay/base` | 7 | `09c0ff33b9987a985584f25ee8a06440443fe1a242e269ab6e4761eb9e40e96e` |
| `tools/overlay/bfmealloc` | 3 | `157e8a32a9e3bbaaca46a16aaf3f746dda8d398a3e6b2113e1286b3f6dfd5b5e` |
| `tools/overlay/bfmealloc_alloconly` | 1 | `0371f7f1d263e491339b93c7af539cc9334d062e6d596b511c12e15c3d74d094` |
| `tools/overlay/bfmehashtable` | 1 | `f945c5a431ed1d3ad36114b57e45085afb1b55cd8ef80282a4fcdffc823d3012` |
| `tools/overlay/bfmelist` | 1 | `9c258d03731204385fd88498669e6f746e5c9fdf3a48c90eb427131e021d25fd` |
| `tools/allocator/stl` | 1 | `2c81e8f109d882af450dbff10c3953b3abf0fbce1e830c7e568678882436ef2b` |
| **All `tools/` combined** | **2,361** | **`bebf44ccd77fbd2881f17ce48aed2655b5c1f0452c72027f15a646188032431b`** |

The 62 DirectX SDK header digests are listed file by file in [`ci/managed-check/dxsdk-includes.manifest`](../ci/managed-check/dxsdk-includes.manifest).

### Approved STLport 4.6 overlay and allocator file digests

| Relative path under `/opt/boat-compiler/tools/` | SHA-256 |
| --- | --- |
| `tools/allocator/README.md` | `50857e1555ca8ef9554e8e526405c502d0f65c7de02323a17ad23c0235fb2c39` |
| `tools/allocator/stl/_alloc.h` | `ca68eb1e65e5135e0fbaeb911e54f8f3bd063d177bad1f8be4f3f22bc3755a1b` |
| `tools/overlay/base/src/c_locale_win32/c_locale_win32.c` | `d35a8c0e41a5f10b9a96fcac03b965a1291820c7b925605143fb490ddc04233f` |
| `tools/overlay/base/stl/_algobase.h` | `da28718641d34c68a92d615ed297a5ed2658f4c5a98ec8ac36ef7d16f082f1f5` |
| `tools/overlay/base/stl/_hashtable.c` | `68de07a2c54831e584d62735f27169f44ac7fccbb56ace2baebe4a948c463e1c` |
| `tools/overlay/base/stl/_list.c` | `7314542d29bae47f098a11015e817fb02d7af79ce5fdb79299f43cb5dd8315b2` |
| `tools/overlay/base/stl/_list.h` | `1085a630afd9b08611d0fbc71e14c6659d08d4a47833d11d1555395d0e0646dd` |
| `tools/overlay/base/stl/_tree.c` | `9ab9a61f85e0cab63f6c3b9df979b41ff047d60ebe04e8d8f2f12496ec872b2e` |
| `tools/overlay/base/stl/_tree.h` | `8be275b800e1e8439d2536b6ed21c49834b5e3c47e10d97ce3045e670895edc2` |
| `tools/overlay/bfmealloc/stl/_algobase.h` | `33e308891c74789c2d4bd3888dcc02e2a73fa5d2970a2373178928dccf06bda9` |
| `tools/overlay/bfmealloc/stl/_alloc.h` | `690bb514ad868a4c411e60153ea0ca25e8537f52b7a1db75ec4538f57fec2381` |
| `tools/overlay/bfmealloc/stl/_uninitialized.h` | `507ffdf1eccc8c5c958c3eff68a0128919002d7de9e7207ab36fd2aca34d4450` |
| `tools/overlay/bfmealloc_alloconly/stl/_alloc.h` | `690bb514ad868a4c411e60153ea0ca25e8537f52b7a1db75ec4538f57fec2381` |
| `tools/overlay/bfmehashtable/stl/_hashtable.h` | `7a8dd0b0739f51d3f65e5f890e99ca3a662b88f3b513270b7383a838b98bc66c` |
| `tools/overlay/bfmelist/stl/_list.h` | `f9818c289a711f6ad7e324e3756dc4b6ef28ff8837bb99ee0e6f9d1d13e89598` |

## Directory layout

| Path | Owner / Mode | Role |
| --- | --- | --- |
| `/opt/boat-compiler/rootfs/` | `root:root`, `0755` | Minimal Ubuntu 24.04 (`noble`) rootfs with Wine `9.0~repack-4build3` (`amd64` + `i386`) and Python 3; bind-mounted read-only as `/` inside `bwrap`. |
| `/opt/boat-compiler/prefix/` | `root:root`, `0755` | Sealed template Wine prefix (`wined3d.dll` and `mshtml.dll` symlinked to the rootfs Wine DLLs so no prefix file exceeds 16 MiB). |
| `/opt/boat-compiler/tools/` | `root:root`, `a+rX,go-w` | User-supplied VC7.1 compiler, runtime DLLs, Platform SDK, DirectX SDK headers, STLport 4.5.3 / 4.6, overlay, and allocator shim; bind-mounted read-only at the same path inside `bwrap`. |
| `/opt/boat-compiler/guard/` | `root:root`, `0444` (`0555` on `pool_launcher.py`) | Runtime isolation and protocol scripts (`pool_bootstrap.sh`, `pool_compiler.py`, `pool_launcher.py`, `pool_network.py`, `pool_probe.py`, `pool_protocol.py`, `pool_worker.py`); bind-mounted read-only at `/ci/guard`. |
| `/opt/boat-compiler/input.sha256` | `root:root`, `0644` | `LC_ALL=C`-sorted SHA-256 manifest of all regular files under `tools/` and `guard/`. |
| `/opt/boat-compiler/runtime-files.sha256` | `root:root`, `0644` | `LC_ALL=C`-sorted SHA-256 manifest of all regular files under `rootfs/` and `prefix/`. |
| `/opt/boat-compiler/runtime-links.tsv` | `root:root`, `0644` | `LC_ALL=C`-sorted symlink path-to-target inventory under `rootfs/` and `prefix/`. |
| `/opt/boat-compiler/runtime-packages.tsv` | `root:root`, `0644` | `LC_ALL=C`-sorted `dpkg-query` package and version inventory of `rootfs/`. |
| `/opt/boat-compiler/image-inventory.json` | `root:root`, `0644` | Top-level JSON sealing the digests of `input.sha256`, `runtime-files.sha256`, `runtime-links.tsv`, `runtime-packages.tsv`, and `cl.exe`. |
| `/opt/boat-compiler/worker.json` | `root:root`, `0644` | Worker profile pinning `compiler_sha256`, `inventory_sha256`, `roots`, `probe_mounts`, `read_only_mounts`, `scratch`, and `timeout_s`. |
| `/var/lib/boat-compiler/jobs` | `ci-compile:ci-compile`, `0700` | Ephemeral per-compile staging directories (created via `/etc/tmpfiles.d/boat-compiler.conf`, on `ext4`). |
| `/var/lib/boat-compiler/stage` | `ci-compile:ci-compile`, `0700` | Ephemeral per-compile Wine prefix and launcher scratch directories. |
| `/run/boat-compiler` | `root:root`, `0755` | Runtime probe output directory. |
| `/usr/local/libexec/bfme2-compiler/run` | `root:root`, `0555` | Fixed entry point called by CI (`probe` or `compile`). |
| `/usr/local/libexec/bfme2-compiler/managed_probe.py` | `root:root`, `0444` | Isolation audit invoked by `/usr/local/libexec/bfme2-compiler/run probe`. |

## Isolation model

1. **Dedicated unprivileged user:** Compilations never run as `root` or the CI runner user. `/usr/local/libexec/bfme2-compiler/run` clears the environment (`env -i PATH=/usr/sbin:/usr/bin:/bin LANG=C PYTHONDONTWRITEBYTECODE=1`) and switches via `setpriv --reuid=ci-compile --regid=ci-compile --clear-groups` into the locked-password account `ci-compile`.
2. **Namespace and mount sandbox (`pool_launcher.py`):** Each translation unit runs inside `bwrap --unshare-all --die-with-parent --cap-drop ALL --clearenv` with a private network namespace, read-only `/` (`rootfs`), `/opt/boat-compiler/tools`, `/ci/guard`, `/ci/job/src`, `/ci/job/include`, and ephemeral writable `/ci/wine`, `/ci/job/out`, and `/tmp`.
3. **Seccomp socket and syscall filter (`pool_network.py`):** Before running Wine or `cl.exe`, `pool_network.py` closes descriptors `>= 3`, sets `PR_SET_NO_NEW_PRIVS`, and installs a BPF seccomp filter for both `x86_64` and `i386` (denying `x32`) that blocks all sockets except `AF_UNIX` (needed by local `wineserver`), as well as `io_uring`, `ptrace`, `bpf`, and `process_vm_*`.
4. **Resource limits (`pool_worker.py` and `pool_compiler.py`):** The outer invocation applies `prlimit --fsize=67108864:67108864 --core=0:0 --cpu=420:430 --nofile=1024:1024` so Wine can initialize its ephemeral `/ci/wine` prefix (`wineboot -i`), removes every DOS drive symlink other than `c:` and `z:`, and then `pool_compiler.py` drops limits to `--fsize=16777216:16777216 --nofile=128:128` before executing `/usr/bin/wine /opt/boat-compiler/tools/vc/Vc7/bin/cl.exe`.
5. **Host hygiene:** The host build disables Docker so `/var/run/docker.sock` is absent, removes `/root/.ssh/authorized_keys` if present, sets a traverse-only ACL (`u:ci-compile:--x`) on `/root` so the probe can confirm `ENOENT` on `/root/.ssh` without reading `/root`, and verifies `GITHUB_TOKEN` / `ACTIONS_RUNTIME_TOKEN` set in the supervisor never enter the compiler process or output.

## Exact compile command and environment

Every compile request submitted to `/usr/local/libexec/bfme2-compiler/run compile` uses the exact rules implemented in [`tools/judge/bin/judge.py`](../tools/judge/bin/judge.py), [`tools/judge/compiler_support.py`](../tools/judge/compiler_support.py), [`ci/managed-nt2/pool_compare.py`](../ci/managed-nt2/pool_compare.py), and [`ci/managed-nt2/pool_worker.py`](../ci/managed-nt2/pool_worker.py):

### Base flags and source markers

- **Ordinary C++ base flags:**
  ```text
  -nologo -c -O2 -GR- -EHsc- -O1 -arch:SSE -G7 -DNDEBUG -MD -EHsc -Gy
  ```
- **Profile exceptions (exact comment line in the TU):**
  - `// cl-profile: upstream` replaces the base flags with `-nologo -c -Gy`.
  - `// cl-arch: x87` removes `-arch:SSE` from the ordinary base flags.
- **Default STLport 4.6 rule (`effective_source`):** Any `.cpp` file under `src/` that is not under `src/zlib-1.1.4/` or `src/lua-4.0.1/` and carries none of `// stlport46`, `// stlport`, or `// msvcstl` is compiled as if it ended with:
  ```cpp
  // stlport46
  // cl: /D_STLP_USE_STATIC_LIB /D_STLP_USE_MALLOC /D_BFME_RETAIL_TREE_INSERT_LAYOUT
  ```
- **Per-TU `// cl:` flags:** Leading `/` is normalized to `-`. Only allowlisted compiler flags (`ALLOWED` in `tools/judge/bin/judge.py` and `FLAG` in `pool_worker.py`), `-W[0-4]`, `-Iinclude/...`, `-Isrc/...`, and `-Ireference/shims/bfmealloc_alloconly` are accepted.
- **STLport, allocator, and SDK include order:**
  1. `// dxsdk` prepends `-I@dx` (`Z:\opt\boat-compiler\tools\dx\Include`) and `-I@vc/Vc7/PlatformSDK/Include`.
  2. `// psdk` or `// platformsdk` prepends `-I@vc/Vc7/PlatformSDK/Include`.
  3. `// stlport46` appends `-I@overlay/bfmealloc_alloconly` (when `// bfmealloc_alloconly` or `-Ireference/shims/bfmealloc_alloconly` is present), followed by `-I@overlay/base` and `-I@stlport46/stlport`.
  4. `// stlport` appends `-I@allocator` (when `bfmealloc_alloconly` is requested) and `-I@stlport45`.
  5. When `bfmealloc_alloconly` is active, `-D_STLP_USE_STATIC_LIB` is added if not already present (`-U_STLP_USE_STATIC_LIB` is refused).

### Invoked command line

Inside `/ci/job`, `pool_worker.py` / `pool_compiler.py` executes:

```text
/usr/bin/wine /opt/boat-compiler/tools/vc/Vc7/bin/cl.exe \
  <base-flags> -showIncludes <sdk-flags> <per-tu-flags-and-stl-includes> -Iinclude \
  -Foout/<index>.obj <tu-with-backslashes>
```

### Environment inside Wine

| Variable | Value inside the sandbox |
| --- | --- |
| `HOME` | `/ci` |
| `PATH` | `/usr/bin:/bin` |
| `WINEPREFIX` | `/ci/wine` |
| `WINEARCH` | `win64` |
| `WINEDEBUG` | `-all` |
| `WINEDLLOVERRIDES` | `mscoree,mshtml=` |
| `LANG` | `C` |
| `LC_ALL` | `C` |
| `INCLUDE` | `Z:\opt\boat-compiler\tools\vc\Vc7\include` |
| `LIB` | `Z:\opt\boat-compiler\tools\vc\Vc7\lib` |
| `WINEPATH` | `Z:\opt\boat-compiler\tools\vc\Vc7\bin;Z:\opt\boat-compiler\tools\vc\Common7\IDE;Z:\opt\boat-compiler\tools\vcruntime` |

### COFF timestamp note

MSVC 7.1 `cl.exe` embeds a 4-byte Unix epoch `TimeDateStamp` in bytes `4..7` of the 20-byte COFF `IMAGE_FILE_HEADER`. Two compiles of identical source at different wall-clock seconds therefore have different raw COFF SHA-256 digests while being **byte-for-byte identical outside bytes `4..7`** (all sections, code bytes, relocations, symbols, and string tables match). Both `tools/compiler-image/control.sh` and `tools/compiler-image/compile_one.sh` report the raw `object_sha256` and the timestamp-normalized `normalized_object_sha256` (bytes `4..7` zeroed) so outputs from different runs and hosts can be compared directly.

## Pinned hashes of `bfme2-compiler-v1`

These digests are pinned by [`ci/managed-check/common.py`](../ci/managed-check/common.py), [`ci/managed-nt2/measure.py`](../ci/managed-nt2/measure.py), and [`.github/workflows/managed-compiler-canary.yml`](../.github/workflows/managed-compiler-canary.yml):

| Artifact | SHA-256 |
| --- | --- |
| Image inventory (`/opt/boat-compiler/image-inventory.json`) | `154f0ee3f79f129b5d2e09adaef61dd2fab208040bff6b64e7fb0e182181dcf6` |
| Worker profile (`/opt/boat-compiler/worker.json`) | `e1f176db430a157b71cfb2f1adffbe5d0464aecb25f7e8796a83e015232ba0e3` |
| VC7.1 `cl.exe` (`/opt/boat-compiler/tools/vc/Vc7/bin/cl.exe`) | `2ecf86a3edfd3deae498e08298e210e984537ce9e11759930561e43f40bd2515` |
| Managed compile entry (`/usr/local/libexec/bfme2-compiler/run`) | `3c5253ceace321aa6855d5f313a951f2db79ab00cbb06bcd78c0c80d08fa7630` |
| Managed probe (`/usr/local/libexec/bfme2-compiler/managed_probe.py`) | `88888c03f6f12eedd455273f0cd131ef7637dba66f83503bf29ed89544b208ab` |
| Pre-snapshot control object (raw COFF, with `TimeDateStamp`) | `59b289e35523a5174c03a40a69b68c36d8c4adec94dd96fdaec099e510b98d83` |
| Pre-snapshot control object (timestamp-normalized COFF) | `e2faff64131aa357f9457b5b05f0b5a56474d44b36c19d68eaf7c97a006052d8` |
| Published `control.sh` object (timestamp-normalized COFF, 517 B) | `e0eab3170bbd3f93ba315effc79fde7eb97d3fcad863550a9c7c0da982e9b095` |
| Published `control.sh` include (`include/control_header.h`) | `619400e59ff9f0eb164332f62fbc04096e5da99c637066393f833ecb4af6c1bd` |

## Building and verifying an image

Run on a fresh dedicated Ubuntu 24.04 (`noble`) `x86_64` machine with `/var/lib` on `ext4`:

```sh
sudo bash tools/compiler-image/build.sh --inputs /path/to/inputs
```

`build.sh` runs four steps in order:

1. `fresh-install.sh --inputs /path/to/inputs` — installs host prerequisites, detaches Docker, creates `ci-compile`, builds the minimal `noble` + Wine `9.0~repack-4build3` rootfs and normalized Wine prefix, copies your inputs into `/opt/boat-compiler/tools/`, installs `/opt/boat-compiler/guard/`, sets `/root` traverse-only ACL (`root-probe-access.sh`), and writes initial manifests.
2. `outer-wine.sh` — installs matching host `wine=9.0~repack-4build3` and `wine64=9.0~repack-4build3`.
3. `seal.sh seal` — records `runtime-files.sha256` and `runtime-links.tsv`, updates `image-inventory.json` and `worker.json`, verifies all manifests, and runs the unprivileged `pool_probe.py` check.
4. `control.sh --install` — installs `/usr/local/libexec/bfme2-compiler/{run,managed_probe.py}`, runs `run probe` with synthetic `GITHUB_TOKEN` and `ACTIONS_RUNTIME_TOKEN` in the supervisor environment, compiles the one-file control with a case-mismatched header include, and verifies bounded `C2065` and `C1189` diagnostics with zero token leakage.

To re-verify an installed image at any time:

```sh
sudo bash tools/compiler-image/seal.sh verify
sudo bash tools/compiler-image/control.sh
```

## Compiling one translation unit

Once the image is installed, compile any translation unit of a checkout through the exact same sealed entry point:

```sh
bash tools/compiler-image/compile_one.sh \
  src/Code/GameEngine/Source/Common/System/UnicodeString.cpp
```

Optional flags: `--repo DIR`, `--out FILE` (write the raw `.obj`), `--json`, and `--show-includes`.

## Publication edits from the `bfme2-compiler-v1` build scripts

The following eight runtime files in `tools/compiler-image/` are **byte-for-byte identical** to `bfme2-compiler-v1`:

| Published path | SHA-256 |
| --- | --- |
| `tools/compiler-image/run` | `3c5253ceace321aa6855d5f313a951f2db79ab00cbb06bcd78c0c80d08fa7630` |
| `tools/compiler-image/managed_probe.py` | `88888c03f6f12eedd455273f0cd131ef7637dba66f83503bf29ed89544b208ab` |
| `tools/compiler-image/guard/pool_bootstrap.sh` | `7653f7cad17101d714dd22442e93663c8a3cab948ab3765eeb3876e88e2e4413` |
| `tools/compiler-image/guard/pool_compiler.py` | `0415f2e4d48bbade6aa3ac1e93749a6e72f1bd91575d7a2ee27d7326645953f0` |
| `tools/compiler-image/guard/pool_launcher.py` | `d8847f4e74fd2fb3aac18e44e82681867740554b29bfa67ed8802c77a86459b0` |
| `tools/compiler-image/guard/pool_network.py` | `cfc9033e8f804fb54ed79b168c3a6c3b59b79303c4e59603810b75e213c02073` |
| `tools/compiler-image/guard/pool_protocol.py` | `b7be2c83cd61275cf4c9feade524bea5825ecb6109a5a5ecee1cdd5879cc7ad4` |
| `tools/compiler-image/guard/pool_worker.py` | `66f54d46f5a7380d19bc86491943d1451bfae9bd667e058ef13e7d837e00e5fb` |

The remaining files were cleaned for public, standalone use with no silent behavioral changes:

- `tools/compiler-image/guard/pool_probe.py` (`8a39fec8ac0326b7e2b742a9f3f0a1fcd68bd588a8ff1f89d683d76fed85db00`): identical to `bfme2-compiler-v1` (`afcb7deccfa25db7ab37ecec628149fc8cb7fef2f3d2a3aebbf78f7277c5b949`) except that six host-specific home-directory strings were removed from `PRIVATE`, leaving the four generic host paths `("/root/.ssh", "/run/secrets", "/run/credentials", "/var/run/docker.sock")`.
- The private SSH forced-command wrapper (`pool_dispatch.py`) and provider-specific farm scripts were omitted; managed and local runs use `/usr/local/libexec/bfme2-compiler/run` directly.
- `wine_socket_direct.c` extracts the exact i386 direct-socket `ld.so.preload` shim (including the Ubuntu 24.04 time64 wrappers `__recvmsg64`, `__sendmsg64`, `__getsockopt64`) as a standalone C source file and installs it under the neutral name `/$LIB/wine-socket-direct.so`.
- `fresh-install.sh` combines the original `debootstrap` rootfs build, Wine `9.0~repack-4build3` + preloader + direct-socket shim installation, Wine prefix initialization/normalization, user creation, and `/opt/boat-compiler` assembly so a user can build directly from `--inputs DIR` instead of a pre-bundled archive.
- `seal.sh` omits internal host path checks and makes deleting `/etc/ssh/ssh_host_*_key` opt-in (`--scrub-ssh-host-keys`) so local or SSH-managed builds do not lose their host keys unexpectedly.
- `control.sh` uses neutral fixture filenames (`src/control_ok.cpp`, `include/control_header.h`, `src/control_bad_id.cpp`, `src/control_bad_directive.cpp`) and tests both `C2065` and `C1189` diagnostics.
- `build.sh`, `compile_one.sh`, and `compile_one.py` were added to drive the build steps in order and compile single translation units from a checkout.

## Live rebuild verification

On `2026-11-21`, `tools/compiler-image/build.sh --inputs <raw-tools-dir>` was run end-to-end on a fresh small Ubuntu 24.04 `x86_64` VM with creator logins disabled, using only the published scripts in `tools/compiler-image/` and the raw `tools/` inputs (`2,361` files, combined listing SHA-256 `bebf44ccd77fbd2881f17ce48aed2655b5c1f0452c72027f15a646188032431b`). The fresh build completed in 189.6 seconds and passed `seal.sh seal` and `control.sh --install`.

### Rebuilt inventory comparison against `bfme2-compiler-v1`

- **`tools/` inputs (`2,361` files) and `cl.exe`:** 100% identical (`bebf44cc...`, `cl.exe` `2ecf86a3...`).
- **Installed entry point and managed probe:** 100% identical (`run` `3c5253ce...`, `managed_probe.py` `88888c03...`).
- **Sealed rootfs package count:** `303` packages in both `bfme2-compiler-v1` and the fresh rebuild (`0` packages added, `0` removed). All Wine (`9.0~repack-4build3`) and Python 3 packages matched identically. Exactly four Ubuntu 24.04 security-update packages advanced by one patch revision between `2026-11-19` and `2026-11-21`:
  - `libsystemd0:amd64`, `libsystemd0:i386`: `255.4-1ubuntu8.18` -> `255.4-1ubuntu8.19`
  - `libudev1:amd64`, `libudev1:i386`: `255.4-1ubuntu8.18` -> `255.4-1ubuntu8.19`
- **Why the top-level inventory SHA-256 differs (`35ae8fa732174d8e89f92ca9575d2af7f1d95aabf816847eda6b2b88030391a3` vs pinned `154f0ee3f79f129b5d2e09adaef61dd2fab208040bff6b64e7fb0e182181dcf6`):**
  1. `runtime_packages_sha256` (`cb888c00...` vs `8649e574...`): the four `libsystemd0`/`libudev1` security-update patch bumps listed above.
  2. `runtime-files.sha256` (`fd8d220f...` vs `de4bccde...`) and `runtime-links.tsv` (`2e8d776b...` vs `1008ce47...`): those four updated `.so` files, newly generated template Wine prefix registry files (not used during compiles because `pool_bootstrap.sh` runs `wineboot -i` into an ephemeral `/ci/wine`), and the neutral `wine-socket-direct.so` filename in `/etc/ld.so.preload`.
  3. `approved_inputs_sha256` (`4f7a2b34...` vs `bfme2-compiler-v1`): the cleaned `guard/pool_probe.py` (`8a39fec8...`) and omission of the private SSH wrapper `pool_dispatch.py`.

### Control and five-file COFF object equivalence against `bfme2-compiler-v1`

Running `control.sh` and `compile_one.sh` on the five translation units from the published comparison in [`tools/README.md`](../tools/README.md) at commit `d759190c771303963709cdf3eb77ab718f43a0cd` produced **byte-for-byte identical timestamp-normalized COFF objects**, identical byte lengths, and identical include dependency lists on both the freshly built image and `bfme2-compiler-v1`:

| Translation unit | Object bytes | Includes | Timestamp-normalized COFF SHA-256 (fresh rebuild = `bfme2-compiler-v1`) |
| --- | ---: | ---: | --- |
| `control.sh` (`src/control_ok.cpp`) | 517 | 1 | `e0eab3170bbd3f93ba315effc79fde7eb97d3fcad863550a9c7c0da982e9b095` |
| `src/Code/GameEngine/Source/GameClient/Gui/GameFont.cpp` | 87,307 | 84 | `830b74b3c3dae8f0119e957b35227a60be4d23161223a9feebed8e5e644d2766` |
| `src/Code/GameEngine/Source/GameLogic/Map/SidesList.cpp` | 81,471 | 87 | `980d15c6cc0985fda368bb9be330c15daaa4545574f6a0c8e5aff59876df8620` |
| `src/Code/GameEngine/Source/GameClient/Gui/GUICallbacks/Apt/AptLanLobby.cpp` | 31,443 | 121 | `23c222ae32d98721e7a9cb8a33809da7b5c72ec7b4c9e13d66826dc0052ab4e2` |
| `src/Code/GameEngine/Source/Common/System/UnicodeString.cpp` | 14,941 | 31 | `82da0a614670626311fd996dccca2c0126fbf9905c94fde2950360246ff36904` |
| `src/zlib-1.1.4/Compression/ZLib/trees.c` | 15,213 | 9 | `32b7cf6101d9a3563df5299f7615d6fdac74f0a9e8092399d11b861028649bb7` |

## Saving a Boat snapshot

After `build.sh` and `control.sh` succeed on a clean small `x86_64` Boat VM started with creator logins disabled (and with `--scrub-ssh-host-keys` passed to `seal.sh`), a maintainer saves the immutable snapshot with `boat snapshot <sandbox-id> <snapshot-name>`. Hosted GitHub Actions jobs then select that snapshot with `runs-on: boat-small/from=<snapshot-name>` (for example, `runs-on: boat-small/from=bfme2-compiler-v1`).
