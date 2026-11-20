# The private nightly image

The link-and-play stage runs on a private Boat snapshot, `bfme2-nightly-v1`. It is built from the private game
snapshot and holds a lawful copy of the game. It is saved in a Boat organization connected only to the private
repository that runs the game (see "Why a pull request cannot reach the game" in [README.md](README.md)). A new
version gets a new name and must pass the private workflow's `probe` run before that workflow names it.

## Layout (`/opt/bfme2-nightly`)

| Path | Holds |
| --- | --- |
| `ref/` | the original program's object files and link inputs: `index.pkl`, `reverse/functions.csv`, `reverse/data_rows.csv`, `build/match/*.obj`, `build/exit_link/` (`retail.def`, initializer, resource, vtable and stub objects, import libraries, `base_repairs.rsp`) |
| `inputs/` | planner inputs: `libguard.json`, `pads.json`, `rebinds.json`, `data_twins.json`, optional `exclude.json`. A file in `ci/nightly/inputs/` on main replaces the image's copy |
| `toolchain/vc71/` | Visual Studio .NET 2003 root (`Vc7/bin/link.exe`, `Common7/IDE/mspdb71.dll`) |
| `toolchain/linkwine/` | a Wine prefix for the linker (copied per run) |
| `game/`, `prefix64/`, `py64/`, `appdata/` | the installed game, its Wine prefix, Windows Python and user data |
| `harness/` | the game test tool, which is not part of this repository (`tools/game_smoke.py` and the tables it reads, and a copy of `baseline/game.dat`) |
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
3. Save the sandbox as `bfme2-nightly-v1` in the separate Boat organization, then run the private workflow with
   `probe`. From this repository, a job that names the image must be refused.
