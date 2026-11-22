"""Tests for Cut 6A: parallel sealed compile RPCs, paired base+head overlap, and LPT wide sharding."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

CHECK = Path(__file__).resolve().parents[1]
ENGINE = CHECK.parent / "managed-nt2"
sys.path.insert(0, str(CHECK))
sys.path.insert(1, str(ENGINE))

import base_cache
import compare
import managed_matrix
import measure
import wide
from pool_protocol import check_object, digest, encode


def _fake_plan(paths, *, side="base"):
    rows = [{"tu": p, "source": digest(p.encode()), "flags": ["-c", "-showIncludes"], "env": {},
             "contract": digest(b"contract-" + p.encode())} for p in paths]
    return {
        "version": 1,
        "historical_base": "a" * 40,
        "historical_head": "b" * 40,
        "base": "a" * 40,
        "head": "b" * 40,
        "tree": "c" * 40,
        "profile_sha256": "1" * 64,
        "image_sha256": "2" * 64,
        "checker": "3" * 64,
        "policy": "4" * 64,
        "changed_paths": list(paths),
        "request_paths": list(paths),
        "compile": {side: rows, ("head" if side == "base" else "base"): list(rows)},
    }


class ParallelCompileTests(unittest.TestCase):
    def test_compile_batch_rpc_runs_concurrently_and_preserves_order(self):
        paths = [f"src/tu_{i}.cpp" for i in range(4)]
        plan = _fake_plan(paths)
        sources = {p: encode(p.encode()) for p in paths}
        hashes = {p: digest(p.encode()) for p in paths}
        barrier = threading.Barrier(2, timeout=5)
        seen_chunks = []
        lock = threading.Lock()

        def fake_request(op, wire):
            self.assertEqual(op, "compile")
            req = json.loads(wire)
            barrier.wait()
            with lock:
                seen_chunks.append([r["tu"] for r in req["plan"]])
            return {
                "version": 1,
                "request": digest(wire),
                "profile": plan["profile_sha256"],
                "results": [{"tu": r["tu"], "source": r["source"], "contract": r["contract"],
                             "status": "error", "diagnostics": "ok"} for r in req["plan"]],
            }

        with patch.object(measure, "projection", return_value=(sources, hashes)), \
             patch.object(measure, "pack_sources", return_value=sources), \
             patch.object(measure, "request", side_effect=fake_request):
            _, _, rows, results, _ = measure.compile_batch_rpc(None, "base", plan, workers=2)
        self.assertEqual([r["tu"] for r in results], paths)
        self.assertEqual(len(seen_chunks), 2)
        self.assertEqual(sorted(seen_chunks), [["src/tu_0.cpp", "src/tu_2.cpp"], ["src/tu_1.cpp", "src/tu_3.cpp"]])

    def test_compile_workers_respects_env_override(self):
        with patch.dict(os.environ, {"BFME_COMPILE_WORKERS": "1"}):
            self.assertEqual(measure.compile_workers(8), 1)
        with patch.dict(os.environ, {"BFME_COMPILE_WORKERS": "3"}):
            self.assertEqual(measure.compile_workers(2), 2)
            self.assertEqual(measure.compile_workers(8), 3)

    def test_measure_pair_overlaps_base_and_head_on_single_tu(self):
        paths = ["src/only.cpp"]
        plan = _fake_plan(paths)
        sources = {p: encode(b"int x;") for p in paths}
        hashes = {p: digest(p.encode()) for p in paths}
        barrier = threading.Barrier(2, timeout=5)

        class FakeGit:
            path = Path("/tmp/fake.git")
            def run(self, *args, **kwargs):
                return type("R", (), {"returncode": 1, "stdout": b""})()
            def changes(self, base, head):
                return [type("C", (), {"path": "src/only.cpp", "mode": "100644"})()]

        def fake_exec(profile, packed, rows):
            barrier.wait()
            return [{"tu": r["tu"], "source": r["source"], "contract": r["contract"],
                     "status": "error", "diagnostics": "err"} for r in rows]

        judged = []
        def fake_judge_compiled(git, judge, side, pl, tools, job, srcs, hsh, rows, results, **kw):
            judged.append((side, [r["tu"] for r in results]))
            return {r["tu"]: {"rows": [], "error": "err", "object_verified": False, "gates": []} for r in rows}

        with patch.dict(os.environ, {"BFME_COMPILE_WORKERS": "2"}), \
             patch.object(measure, "projection", return_value=(sources, hashes)), \
             patch.object(measure, "pack_sources", return_value=sources), \
             patch.object(measure, "execute_compile_rpc", side_effect=fake_exec), \
             patch.object(measure, "judge_compiled", side_effect=fake_judge_compiled):
            old, new = compare.measure_pair(FakeGit(), object(), plan, {}, Path("/tmp/b"), Path("/tmp/h"), cache_dir="")
        self.assertEqual(list(old), paths)
        self.assertEqual(list(new), paths)
        self.assertEqual(judged, [("base", paths), ("head", paths)])

    def test_balanced_chunks_eliminates_single_tu_tail(self):
        self.assertEqual(wide.balanced_chunks(9, 8), [(0, 5), (5, 9)])
        self.assertEqual(wide.balanced_chunks(10, 8), [(0, 5), (5, 10)])
        self.assertEqual(wide.balanced_chunks(8, 8), [(0, 8)])
        self.assertEqual(wide.balanced_chunks(1, 8), [(0, 1)])
        self.assertEqual(wide.balanced_chunks(0, 8), [])

    def test_lpt_weights_spread_heavy_tus_across_shards(self):
        paths = [f"src/f{i}.cpp" for i in range(6)]
        scope = _fake_plan(paths)
        commands = {
            "base": [{"tu": p, "source": digest(p.encode()), "flags": ["-c", "-showIncludes"],
                      "env": {}, "contract": digest(b"c" + p.encode())} for p in paths],
            "head": [{"tu": p, "source": digest(b"h" + p.encode()), "flags": ["-c", "-showIncludes"],
                      "env": {}, "contract": digest(b"c" + p.encode())} for p in paths],
        }
        weights = {"src/f0.cpp": 500_000, "src/f1.cpp": 480_000, "src/f2.cpp": 1000,
                   "src/f3.cpp": 1000, "src/f4.cpp": 1000, "src/f5.cpp": 1000}
        doc = managed_matrix.make(scope, commands, limit=2, weights=weights)
        shard_tus = [sorted({r["tu"] for r in s["compile"]}) for s in doc["partition"]["shards"]]
        # The two 500 KB heavy TUs must land on different shards
        self.assertNotEqual("src/f0.cpp" in shard_tus[0], "src/f1.cpp" in shard_tus[0])

    def test_base_cache_uses_dynamic_asm_allowlist_config(self):
        """Regression test: all-hit base cache batch must honor asm_allowlist.json added after import."""
        orig_cfg = measure.CONFIG
        try:
            with tempfile.TemporaryDirectory() as tmp:
                job = Path(tmp) / "job"
                copied = []
                def fake_data_entry(git, rev, name, root, **kw):
                    copied.append(name)
                    target = root / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("{}")

                class FakeJudge:
                    def ledger(self, j): return {}
                    def effective_source(self, name, raw): return raw
                    def judge_tu(self, j, tu, l): return {"rows": [], "gates": [], "object_verified": True}

                plan = _fake_plan(["src/a.cpp"])
                sources = {"src/a.cpp": encode(b"int a;")}
                hashes = {"src/a.cpp": digest(b"int a;")}
                cache_file = Path(tmp) / "entry.json.gz"
                cache_file.write_bytes(b"")
                hit = {
                    "cache_path": cache_file,
                    "row": plan["compile"]["base"][0],
                    "object_sha256": "5" * 64,
                    "object_bytes": b"obj",
                    "verified_source": [],
                    "verified_sealed": [],
                }
                measure.CONFIG = (*orig_cfg, "asm_allowlist.json")
                with patch.object(base_cache, "data_entry", side_effect=fake_data_entry):
                    base_cache.finish_base_cache(
                        None, FakeJudge(), plan, {}, job, Path(tmp) / "cache",
                        sources, hashes, {"src/a.cpp": hit}, [], {},
                    )
                self.assertIn("config/asm_allowlist.json", copied)
        finally:
            measure.CONFIG = orig_cfg

    def test_weighted_sharding_respects_32_tu_recovery_cap(self):
        """Regression test: extreme weight skew on 36 TUs across 4 shards never exceeds 32 TUs/shard."""
        import wide_recovery
        paths = [f"src/f{i:02d}.cpp" for i in range(36)]
        scope = _fake_plan(paths)
        commands = {
            "base": [{"tu": p, "source": digest(p.encode()), "flags": ["-c", "-showIncludes"],
                      "env": {}, "contract": digest(b"c" + p.encode())} for p in paths],
            "head": [{"tu": p, "source": digest(b"h" + p.encode()), "flags": ["-c", "-showIncludes"],
                      "env": {}, "contract": digest(b"c" + p.encode())} for p in paths],
        }
        weights = {p: (1_000_000 if i < 3 else 10) for i, p in enumerate(paths)}
        doc = managed_matrix.make(scope, commands, limit=4, weights=weights,
                                  max_tus_per_shard=wide.MAX_SHARD_TUS)
        counts = [len(s["compile"]) // 2 for s in doc["partition"]["shards"]]
        self.assertTrue(all(c <= wide.MAX_SHARD_TUS for c in counts), counts)
        self.assertEqual(sum(counts), 36)
        # wide_recovery.groups(doc) must accept the plan
        groups = wide_recovery.groups(doc)
        self.assertTrue(groups)

    def test_measure_pair_bounds_total_rpcs_to_workers_and_records_timing_on_error(self):
        """Regression tests for P2s: total RPCs <= workers, and failed RPC still records elapsed time."""
        paths = [f"src/f{i}.cpp" for i in range(8)]
        plan = _fake_plan(paths)
        sources = {p: encode(b"int x;") for p in paths}
        hashes = {p: digest(p.encode()) for p in paths}

        class FakeGit:
            path = Path("/tmp/fake.git")
            def run(self, *args, **kwargs):
                return type("R", (), {"returncode": 1, "stdout": b""})()
            def changes(self, base, head):
                return [type("C", (), {"path": p, "mode": "100644"})() for p in paths]

        rpc_calls = []
        def fake_exec(profile, packed, rows):
            rpc_calls.append(len(rows))
            return [{"tu": r["tu"], "source": r["source"], "contract": r["contract"],
                     "status": "error", "diagnostics": "err"} for r in rows]

        def fake_judge_compiled(git, judge, side, pl, tools, job, srcs, hsh, rows, results, **kw):
            return {r["tu"]: {"rows": [], "error": "err", "object_verified": False, "gates": []} for r in rows}

        with patch.dict(os.environ, {"BFME_COMPILE_WORKERS": "4"}),              patch.object(measure, "projection", return_value=(sources, hashes)),              patch.object(measure, "pack_sources", return_value=sources),              patch.object(measure, "execute_compile_rpc", side_effect=fake_exec),              patch.object(measure, "judge_compiled", side_effect=fake_judge_compiled):
            compare.measure_pair(FakeGit(), object(), plan, {}, Path("/tmp/b"), Path("/tmp/h"), cache_dir="")
        self.assertLessEqual(len(rpc_calls), 4, f"Expected <=4 RPCs on 4 workers, got {rpc_calls}")

        # Now verify failed RPC records non-zero compile time in base_timing
        import time as _time
        def slow_fail(profile, packed, rows):
            _time.sleep(0.02)
            raise RuntimeError("boom")
        b_timing = {}
        with patch.dict(os.environ, {"BFME_COMPILE_WORKERS": "2"}),              patch.object(measure, "projection", return_value=(sources, hashes)),              patch.object(measure, "pack_sources", return_value=sources),              patch.object(measure, "execute_compile_rpc", side_effect=slow_fail):
            with self.assertRaises(RuntimeError):
                compare.measure_pair(FakeGit(), object(), plan, {}, Path("/tmp/b"), Path("/tmp/h"),
                                     cache_dir="", base_timing=b_timing)
        self.assertGreater(b_timing.get("compile", 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
