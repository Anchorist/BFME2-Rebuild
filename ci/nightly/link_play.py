"""Nightly stage 2: plan the hybrid image, link it, check it, play it and compare it with the original.

  python3 -B ci/nightly/link_play.py SHARDS_DIR OUT_DIR [--no-game]

Runs only on the private nightly image (layout in ci/nightly/IMAGE.md). The reference objects, the game's assets and
the original's checksum records stay on that image: this step writes counts, verdicts and hashes to
OUT_DIR/stage2.json and nothing else leaves the machine.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from time import monotonic

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from checks import TESTS, crc_compare, judge_test, reload_compare, merge_shards  # noqa: E402
from scrub import scrub  # noqa: E402

IMAGE = Path(os.environ.get("BFME_NIGHTLY_IMAGE", "/opt/bfme2-nightly"))


class Stop(Exception):
    pass


def expect(ok, expected, found):
    if not ok:
        raise Stop(f"expected {expected}; found {found}")


def verify_image(out):
    manifest = IMAGE / "MANIFEST.sha256"
    expect(manifest.is_file(), f"the nightly image manifest at {manifest}", "no such file")
    r = subprocess.run(["sha256sum", "-c", "--quiet", "MANIFEST.sha256"], cwd=IMAGE, capture_output=True, text=True)
    bad = [l for l in r.stdout.splitlines() if l.strip()]
    expect(r.returncode == 0, "every file of the nightly image to match its manifest",
           f"{len(bad)} differing files, first: {bad[0].split(':')[0] if bad else r.stderr.strip()[:200]}")
    return subprocess.run(["sha256sum", "MANIFEST.sha256"], cwd=IMAGE, capture_output=True, text=True).stdout.split()[0]


def prepare_work(work, sha):
    work.mkdir(parents=True, exist_ok=True)
    (work / "base").mkdir(exist_ok=True)
    if not (work / "base/ref").exists():
        (work / "base/ref").symlink_to(IMAGE / "ref")
    if (work / "inputs").exists():
        shutil.rmtree(work / "inputs")
    shutil.copytree(IMAGE / "inputs", work / "inputs")
    if (ROOT / "inputs").is_dir():
        shutil.copytree(ROOT / "inputs", work / "inputs", dirs_exist_ok=True)
    if (work / "planner").exists():
        shutil.rmtree(work / "planner")
    shutil.copytree(ROOT / "planner", work / "planner")
    if not (work / "wine").exists():
        shutil.copytree(IMAGE / "toolchain/linkwine", work / "wine", symlinks=True)
    os.environ.update(NIGHTLY_WORK=str(work), NIGHTLY_GIT_DIR=str(Path.cwd() / ".git"),
                      NIGHTLY_BASELINE=str(Path.cwd() / "baseline/game.dat"),
                      NIGHTLY_VC_ROOT=str(IMAGE / "toolchain/vc71"), VC71_ROOT=str(IMAGE / "toolchain/vc71"),
                      NIGHTLY_BUILD_TOOLS=str(ROOT.parent / "managed-nt2/engine/reference"),
                      NIGHTLY_REMOTE_LINK="0")
    sys.path.insert(0, str(work / "planner"))


def stage_link(work, sha, shards_dir, result):
    import hybrid
    rb = hybrid.Rebuild(sha)
    files = rb.files()
    results, shard_info = merge_shards(shards_dir, sha, files)
    result["compile"] = shard_info
    obj_dir = rb.tree / "obj"
    obj_dir.mkdir(exist_ok=True)
    for d in sorted(Path(shards_dir).iterdir()):
        for f in sorted((d / "obj").glob("*")) if (d / "obj").is_dir() else []:
            shutil.copyfile(f, obj_dir / f.name)
    (rb.work / "judge_all.json").write_text(json.dumps({"summary": {"sha": sha, "via": "nightly compile"},
                                                         "results": results}))
    t0 = monotonic()
    res = hybrid.run(sha, ["matching"], True, work / "run", stubs=True, base="ref")["matching"]
    link = res.get("link") or {}
    lk = res["linkable"]
    result["plan"] = {"candidate_files": res["files"], "compiled": res["compiled"], "files": lk["files"],
                      "functions": lk["functions"], "excluded": len(lk["excluded"]),
                      "excluded_files": sorted(lk["excluded"]),
                      "predicted_unresolved": lk["predicted_unresolved"],
                      "predicted_duplicates": lk["predicted_duplicates"], "bridges": lk["bridges"],
                      "guard": (lk.get("libguard") or {}).get("counts")}
    result["link"] = {"image": bool(link.get("image")), "unresolved": len(link.get("unresolved") or []),
                      "duplicates": len(link.get("duplicates") or []), "seconds": link.get("seconds"),
                      "first_errors": [e.split(":", 1)[-1].strip()[:160] for e in (link.get("errors") or [])[:5]]}
    result["timings"]["plan_and_link_s"] = round(monotonic() - t0, 1)
    expect(link.get("image") and not link.get("unresolved") and not link.get("duplicates"),
           "a linked image with 0 unresolved and 0 duplicate names",
           f"image={bool(link.get('image'))} unresolved={len(link.get('unresolved') or [])} "
           f"duplicates={len(link.get('duplicates') or [])}")
    tier = work / "run/matching"
    import hashlib
    result["image_sha256"] = hashlib.sha256((tier / "exit.exe").read_bytes()).hexdigest()
    return tier, rb


def stage_static(work, sha, tier, rb, result):
    t0 = monotonic()
    r = subprocess.run([sys.executable, "-B", str(work / "planner/extents.py"), str(tier), sha, "--base", "ref",
                        "--src-objs", str(rb.tree / "obj"), "--out", str(tier / "extents.tsv"),
                        "--json", str(tier / "extents.json")], capture_output=True, text=True)
    expect(r.returncode == 0 and (tier / "extents.json").is_file(), "the size check to run",
           f"exit {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}")
    ex = json.loads((tier / "extents.json").read_text())
    result["size_check"] = {"findings": ex["findings"], "new": ex["new"], "blocking": ex["blocking"],
                            "seconds": round(monotonic() - t0, 1)}
    expect(ex["blocking"] == 0, "no blocking size finding in the planned image", f"{ex['blocking']} blocking findings")


def stage_game(tier, result, outdir):
    image = tier / "exit.exe"
    for test in TESTS:
        t0 = monotonic()
        jobdir = outdir / "games" / test["name"]
        jobdir.mkdir(parents=True, exist_ok=True)
        limit = test["timeout"] + 900
        try:
            r = subprocess.run(["bash", str(ROOT / "play.sh"), str(jobdir), str(image), str(IMAGE), test["tool"]]
                               + test["args"], capture_output=True, text=True, timeout=limit)
            rc, log = r.returncode, (r.stdout or "")[-20000:] + (r.stderr or "")[-20000:]
        except subprocess.TimeoutExpired:
            subprocess.run(["wineserver", "-k"], capture_output=True, check=False)
            rc, log = -9, f"expected the run to end within {limit} s; found it still running"
        (jobdir / "play.log").write_text(log)
        found = {}
        out = jobdir / "out"
        if test["kind"] == "record":
            recs = sorted(out.glob("record*.json"))
            if recs:
                control = json.loads((IMAGE / "records" / test["control"]).read_text())
                found = crc_compare(control, json.loads(recs[0].read_text()), test["until"])
        else:
            rel = out / "reload_real.json"
            if rel.is_file():
                control = json.loads((IMAGE / "records" / test["control"]).read_text())
                found = reload_compare(control, json.loads(rel.read_text()))
        done = json.loads((out / "done.json").read_text()) if (out / "done.json").is_file() else {}
        verdict = judge_test(test, found, rc, done)
        verdict["seconds"] = round(monotonic() - t0, 1)
        result["tests"][test["name"]] = verdict
        print(f"Nightly game test {test['name']}: {verdict['status']} - {verdict['detail']}", flush=True)
        if test["name"] == "udun" and verdict["status"] != "pass":
            break


def probe():
    """Startup probe of a new image: every check prints one line; exit 1 at the first failure."""
    try:
        print(f"probe: image manifest verified, digest {verify_image(None)}", flush=True)
        for rel in ("ref/index.pkl", "ref/build/exit_link/retail.def", "inputs/libguard.json", "harness/tools/game_smoke.py",
                    "toolchain/vc71/Vc7/bin/link.exe", "game", "prefix64/dosdevices", "py64/python.exe", "appdata",
                    *("records/" + t["control"] for t in TESTS)):
            expect((IMAGE / rel).exists(), f"{IMAGE / rel} on the image", "nothing")
        print("probe: every input of the nightly is present", flush=True)
        for cmd in ("wine", "wineserver", "Xvfb", "xauth", "mcookie", "git", "sha256sum"):
            expect(shutil.which(cmd) is not None, f"the command {cmd}", "none on PATH")
        print("probe: wine, Xvfb, xauth, mcookie, git and sha256sum are installed", flush=True)
        expect(sys.version_info >= (3, 10), "Python 3.10 or newer", sys.version.split()[0])
        prefix = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "bfme-probe-wine"
        shutil.rmtree(prefix, ignore_errors=True)
        shutil.copytree(IMAGE / "toolchain/linkwine", prefix, symlinks=True)
        r = subprocess.run(["wine", str(IMAGE / "toolchain/vc71/Vc7/bin/link.exe"), "/?"], capture_output=True, text=True,
                           env=dict(os.environ, WINEPREFIX=str(prefix), WINEDEBUG="-all"), timeout=300)
        expect("Microsoft (R) Incremental Linker" in r.stdout, "link.exe to print its banner under Wine",
               (r.stdout + r.stderr).strip()[:200] or f"exit {r.returncode} and no output")
        print("probe: link.exe runs under Wine", flush=True)
        expect("GITHUB_TOKEN" not in os.environ, "no token in the probe's environment", "GITHUB_TOKEN set")
        print("probe: PASS", flush=True)
        return 0
    except Stop as e:
        print(f"probe: FAIL: {e}", flush=True)
        return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shards", nargs="?")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--no-game", action="store_true")
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()
    if a.probe:
        return probe()
    if not (a.shards and a.out):
        print("nightly link-and-play: expected arguments SHARDS_DIR OUT_DIR; found none", file=sys.stderr)
        return 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sha = os.environ.get("NIGHTLY_SHA") or os.environ.get("GITHUB_SHA", "")
    result = {"stage": "link-and-play", "sha": sha, "timings": {}, "tests": {}, "stopped": None,
              "games_skipped": bool(a.no_game)}
    started = monotonic()
    try:
        result["image_manifest_sha256"] = verify_image(out)
        work = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "bfme-nightly-work"
        prepare_work(work, sha)
        tier, rb = stage_link(work, sha, a.shards, result)
        stage_static(work, sha, tier, rb, result)
        if not a.no_game:
            stage_game(tier, result, out)
    except Stop as e:
        result["stopped"] = str(e)
        print(f"nightly link-and-play: {e}", file=sys.stderr, flush=True)
    except Exception as e:  # noqa: BLE001  (reported, never silent)
        result["stopped"] = f"expected the step to finish; found {type(e).__name__}: {str(e)[:300]}"
        print(f"nightly link-and-play: {result['stopped']}", file=sys.stderr, flush=True)
    result["timings"]["stage_s"] = round(monotonic() - started, 1)
    (out / "stage2.json").write_text(json.dumps(scrub(result), indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
