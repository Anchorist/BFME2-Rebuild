"""The nightly game tests, the checksum comparison and the verdict of each test. Pure functions, tested offline."""
import json
from pathlib import Path

UDUN = r"maps\map mp tournament udun.map"
FORDS = r"maps\map mp fords of isen ii.map"

# Each recorded run is compared with the original program's record of the same map, seed and frames.
TESTS = [
    {"name": "udun", "kind": "record", "tool": "game_smoke.py", "control": "udun-1000.json", "until": 1000,
     "expect_frames": 40, "timeout": 3600,
     "args": ["record", "--map", UDUN, "--seed", "1", "--until-frame", "1000", "--crc-every", "25", "--timeout", "3600"]},
    {"name": "control", "kind": "record", "tool": "game_smoke.py", "control": "udun-1000.json", "until": 1000,
     "expect_frames": 40, "timeout": 3600, "perturb": 500,
     "args": ["record", "--map", UDUN, "--seed", "1", "--until-frame", "1000", "--crc-every", "25", "--timeout", "3600",
              "--perturb-frame", "500"]},
    {"name": "fords", "kind": "record", "tool": "game_smoke.py", "control": "fords-1000.json", "until": 1000,
     "expect_frames": 40, "timeout": 3600,
     "args": ["record", "--map", FORDS, "--seed", "2", "--until-frame", "1000", "--crc-every", "25", "--timeout", "3600"]},
    {"name": "long", "kind": "record", "tool": "game_smoke.py", "control": "udun-5000.json", "until": 5000,
     "expect_frames": 200, "timeout": 6000,
     "args": ["record", "--map", UDUN, "--seed", "1", "--until-frame", "5000", "--crc-every", "25", "--timeout", "6000"]},
    {"name": "save", "kind": "reload", "tool": "game_smoke.py", "control": "reload.json", "timeout": 1500,
     "args": ["reload", "--player", "--seed", "1", "--until-frame", "600", "--crc-every", "25", "--timeout", "1500"]},
]


def _frames(table):
    return {int(k): v for k, v in dict(table or {}).items()}


def crc_compare(control, run, until=None):
    """Frames both records hold (up to `until`), how many are equal, the first that differs, the last frame run."""
    c, h = _frames(control.get("crcs")), _frames(run.get("crcs"))
    if until is not None:
        c = {f: v for f, v in c.items() if f <= until}
    frames = sorted(set(c) & set(h))
    first = next((f for f in frames if c[f] != h[f]), None)
    return {"frames_compared": len(frames), "frames_equal": sum(c[f] == h[f] for f in frames),
            "first_divergent_frame": first, "last_frame": max(h, default=None), "control_frames": len(c)}


def reload_compare(control, run):
    def cmp(a, b):
        a, b = _frames(a), _frames(b)
        fr = sorted(set(a) & set(b))
        return {"frames_compared": len(fr), "frames_equal": sum(a[f] == b[f] for f in fr),
                "first_divergent_frame": next((f for f in fr if a[f] != b[f]), None)}
    return {"outcome": run.get("outcome"), "after_load": cmp(control.get("crcs"), run.get("crcs")),
            "before_load": cmp(control.get("crcs_before_load"), run.get("crcs_before_load"))}


def judge_test(test, found, rc, done=None):
    """status: pass | differs | crash | control-blind. `detail` says what was expected and what was found."""
    done = done or {}
    base = {"name": test["name"], "game_exit": done.get("rc", rc)}
    if test["kind"] == "reload":
        if not found:
            return dict(base, status="crash", detail="expected a save/load record; found none (the game did not finish)")
        a, b = found["after_load"], found["before_load"]
        out = dict(base, outcome=found["outcome"], after_load=a, before_load=b)
        if found["outcome"] != "pass" and a["frames_compared"] == 0:
            return dict(out, status="crash", detail=f"expected outcome pass; found {found['outcome']!r} with no frames after the load")
        for label, part in (("before the save", b), ("after the load", a)):
            if part["frames_compared"] == 0:
                return dict(out, status="crash", detail=f"expected checksum frames {label}; found none")
            if part["first_divergent_frame"] is not None:
                return dict(out, status="differs", first_divergent_frame=part["first_divergent_frame"],
                            detail=f"expected every frame {label} equal; first differing frame {part['first_divergent_frame']}")
        if found["outcome"] != "pass":
            return dict(out, status="crash", detail=f"expected outcome pass; found {found['outcome']!r}")
        return dict(out, status="pass", detail=f"after the load {a['frames_equal']}/{a['frames_compared']} equal, "
                                              f"before {b['frames_equal']}/{b['frames_compared']}")
    if not found:
        return dict(base, status="crash", detail="expected a checksum record; found none (the game did not start or crashed)")
    out = dict(base, frames_compared=found["frames_compared"], frames_equal=found["frames_equal"],
               first_divergent_frame=found["first_divergent_frame"], last_frame=found["last_frame"])
    first, want = found["first_divergent_frame"], test["expect_frames"]
    if "perturb" in test:
        if first == test["perturb"]:
            return dict(out, status="pass", detail=f"the deliberately changed run was caught at frame {first}")
        if first is None:
            return dict(out, status="control-blind",
                        detail=f"expected the changed run to differ at frame {test['perturb']}; found no difference "
                               f"in {found['frames_compared']} frames, so the comparison cannot be trusted")
        return dict(out, status="control-blind",
                    detail=f"expected the changed run to differ first at frame {test['perturb']}; found frame {first}")
    if first is not None:
        return dict(out, status="differs", detail=f"expected {want} equal frames; first differing frame {first} "
                                                   f"({found['frames_equal']}/{found['frames_compared']} equal)")
    if found["frames_compared"] < want:
        return dict(out, status="crash", detail=f"expected {want} compared frames; found {found['frames_compared']} "
                                                 f"(last frame reached {found['last_frame']})")
    return dict(out, status="pass", detail=f"{found['frames_equal']}/{found['frames_compared']} frames equal")


def merge_shards(shards_dir, sha, files):
    """Join the compile shards; refuse a missing, foreign, duplicated or incomplete shard."""
    infos, results = [], {}
    for d in sorted(Path(shards_dir).iterdir()):
        if not (d / "shard.json").is_file():
            continue
        info = json.loads((d / "shard.json").read_text())
        if info["sha"] != sha:
            raise ValueError(f"expected compile shards of {sha}; found one of {info['sha']}")
        infos.append(info)
        for line in (d / "judge.jsonl").read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r["tu"] in results:
                    raise ValueError(f"expected each file in one shard; found {r['tu']} twice")
                results[r["tu"]] = r
    n = {i["shards"] for i in infos}
    if len(n) != 1 or sorted(i["shard"] for i in infos) != list(range(n.pop())):
        raise ValueError(f"expected every compile shard once; found shards {sorted(i['shard'] for i in infos)}")
    missing = sorted(set(files) - set(results))
    if missing or set(results) - set(files):
        raise ValueError(f"expected a judge result for each of {len(files)} source files; found {len(results)} "
                         f"(missing {len(missing)}, first {missing[:1]})")
    summary = {k: sum(i[k] for i in infos) for k in ("files", "compiled", "compile_errors", "fully_matching")}
    summary["shards"] = len(infos)
    summary["slowest_shard_s"] = max(i["seconds"] for i in infos)
    return [results[t] for t in sorted(results)], summary
