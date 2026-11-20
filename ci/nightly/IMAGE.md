# The private nightly image

The link-and-play stage runs on a private Boat snapshot, `bfme2-nightly-v1`. It is built from the private game
snapshot and holds a lawful copy of the game. It is never public and never serves a pull request. A new version
gets a new name and must pass the probe (`Run workflow` with `probe`) before the repository variable points to it.

## Layout (`/opt/bfme2-nightly`)

| Path | Holds |
| --- | --- |
| `ref/` | the original program's object files and link inputs: `index.pkl`, `reverse/functions.csv`, `reverse/data_rows.csv`, `build/match/*.obj`, `build/exit_link/` (`retail.def`, initializer, resource, vtable and stub objects, import libraries, `base_repairs.rsp`) |
| `inputs/` | planner inputs: `libguard.json`, `pads.json`, `rebinds.json`, `data_twins.json`, optional `exclude.json`. A file in `ci/nightly/inputs/` on main replaces the image's copy |
| `toolchain/vc71/` | Visual Studio .NET 2003 root (`Vc7/bin/link.exe`, `Common7/IDE/mspdb71.dll`) |
| `toolchain/linkwine/` | a Wine prefix for the linker (copied per run) |
| `game/`, `prefix64/`, `py64/`, `appdata/` | the installed game, its Wine prefix, Windows Python and user data |
| `harness/` | the game test tool (`tools/game_smoke.py` and the tables it reads, `baselines/.../game.dat`, equal to `baseline/game.dat`) |
| `records/` | the original program's recordings: `udun-1000.json`, `udun-5000.json`, `fords-1000.json`, `reload.json` |
| `MANIFEST.sha256` | SHA-256 of every file above except the Wine prefixes and user data; checked at the start of every run |

Software: Wine 9 (64-bit with 32-bit support), Xvfb, xauth, mcookie, Python 3.10 or newer, git, sha256sum. The
runner account reads `/opt/bfme2-nightly` and writes only to its job's temporary directory. Machine: the size the
game box uses (Boat `default`).

## Building it

1. Restore a fresh sandbox from the game snapshot. Copy the payload archive (the layout above without the game,
   prefixes and manifest) into it.
2. Run the install script as root with the payload's expected SHA-256. It refuses a different payload, links the
   game install, creates the linker's Wine prefix, writes `MANIFEST.sha256` and checks that `link.exe` runs.
3. Save the sandbox as `bfme2-nightly-v1`. Set the repository variable `BFME_NIGHTLY_GAME_RUNNER` to its runner
   label only after the probe passes, and only if Boat serves that label to this repository's default-branch
   workflows alone.
