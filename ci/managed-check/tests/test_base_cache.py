import json
import sys
import tempfile
import unittest
from hashlib import sha256
from pathlib import Path
from unittest import mock

MC = Path(__file__).resolve().parents[1]
NT2 = Path(__file__).resolve().parents[2] / "managed-nt2"
sys.path.insert(0, str(MC))
sys.path.insert(1, str(NT2))

import base_cache
from pool_protocol import encode


import struct


def make_coff(tag=b"\xc3"):
    # Minimal valid 32-bit x86 COFF: 1 .text section, 1 symbol, 4-byte string table.
    raw_at = 20 + 40
    raw = bytes(tag)
    sym_at = raw_at + len(raw)
    hdr = struct.pack("<HHLLLHH", 0x014C, 1, 0, sym_at, 1, 0, 0)
    sec = struct.pack("<8sLLLLLLHHL", b".text\x00\x00\x00", 0, 0, len(raw), raw_at, 0, 0, 0, 0, 0x60000020)
    sym = struct.pack("<8sLhhBB", b"_f\x00\x00\x00\x00\x00\x00", 0, 1, 0x20, 2, 0)
    strs = struct.pack("<L", 4)
    return hdr + sec + raw + sym + strs


class BaseCacheTests(unittest.TestCase):
    def _fixture(self, tmp):
        root = Path(tmp)
        tools_dir = root / "tools" / "vc"
        tools_dir.mkdir(parents=True)
        sealed_hdr = tools_dir / "stddef.h"
        sealed_hdr.write_bytes(b"typedef unsigned int size_t;\n")
        sealed_sha = sha256(sealed_hdr.read_bytes()).hexdigest()

        job = root / "job"
        (job / "src").mkdir(parents=True)
        (job / "include").mkdir(parents=True)
        (job / "obj").mkdir(parents=True)

        tu_bytes = b'#include "Foo.h"\nint f() { return 1; }\n'
        hdr_bytes = b"int f();\n"
        tu_sha = sha256(tu_bytes).hexdigest()
        hdr_sha = sha256(hdr_bytes).hexdigest()
        (job / "src/Foo.cpp").write_bytes(tu_bytes)
        (job / "include/Foo.h").write_bytes(hdr_bytes)

        obj_bytes = make_coff(b"body1")
        obj_sha = sha256(obj_bytes).hexdigest()
        obj = job / "obj/src_Foo.cpp.obj"
        obj.write_bytes(obj_bytes)
        obj.with_suffix(".obj.compile.json").write_text(json.dumps({
            "source_sha256": tu_sha,
            "object_sha256": obj_sha,
            "headers": {str(job / "include/Foo.h"): hdr_sha, str(sealed_hdr): sealed_sha},
            "compiler_contract": "c" * 64,
        }))

        row = {"tu": "src/Foo.cpp", "source": tu_sha, "contract": "c" * 64}
        plan = {"profile_sha256": "p" * 64, "image_sha256": "i" * 64, "historical_base": "b" * 40,
                "request_paths": ["src/Foo.cpp"], "compile": {"base": [row]}}
        sources = {"src/Foo.cpp": encode(tu_bytes), "include/Foo.h": encode(hdr_bytes)}
        hashes = {"src/Foo.cpp": tu_sha, "include/Foo.h": hdr_sha}
        tools = {"vc": str(tools_dir)}
        return root, job, row, plan, sources, hashes, tools, obj_sha, sealed_hdr

    def test_store_verify_materialize_and_invalidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, job, row, plan, sources, hashes, tools, obj_sha, sealed_hdr = self._fixture(tmp)
            cache = root / "cache"
            self.assertTrue(base_cache.store(cache, row, plan, job, tools, hashes))
            hit = base_cache.verify_hit(cache, row, plan, sources, hashes, tools)
            self.assertIsNotNone(hit)
            job2 = root / "job2"
            obj2 = base_cache.materialize_hit(hit, sources, job2)
            self.assertEqual(sha256(obj2.read_bytes()).hexdigest(), obj_sha)
            hashes_changed = dict(hashes)
            hashes_changed["include/Foo.h"] = "f" * 64
            self.assertIsNone(base_cache.verify_hit(cache, row, plan, sources, hashes_changed, tools))
            # Adding a shadowing header beside the TU MUST miss even if all recorded hashes match.
            hashes_shadow = dict(hashes, **{"src/Foo.h": "e" * 64})
            self.assertIsNone(base_cache.verify_hit(cache, row, plan, sources, hashes_shadow, tools))
            sealed_hdr.write_bytes(b"typedef long size_t;\n")
            self.assertIsNone(base_cache.verify_hit(cache, row, plan, sources, hashes, tools))

    def test_corrupted_entry_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, job, row, plan, sources, hashes, tools, _, _ = self._fixture(tmp)
            cache = root / "cache"
            self.assertTrue(base_cache.store(cache, row, plan, job, tools, hashes))
            key = base_cache.entry_key(row, plan)
            (cache / key[:2] / f"{key}.json.gz").write_bytes(b"corrupt")
            self.assertIsNone(base_cache.verify_hit(cache, row, plan, sources, hashes, tools))
            # Valid gzip magic with truncated/corrupt deflate payload (triggers zlib.error) must also fail closed.
            (cache / key[:2] / f"{key}.json.gz").write_bytes(bytes([0x1F, 0x8B, 0x08, 0x00, 0, 0, 0, 0, 0, 0xFF, 0xFF]))
            self.assertIsNone(base_cache.verify_hit(cache, row, plan, sources, hashes, tools))

    def test_partial_hit_runs_measure_only_on_misses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, job, row, plan, sources, hashes, tools, _, _ = self._fixture(tmp)
            tu2_bytes = b"int g() { return 2; }\n"
            tu2_sha = sha256(tu2_bytes).hexdigest()
            row2 = {"tu": "src/Bar.cpp", "source": tu2_sha, "contract": "c" * 64}
            sources["src/Bar.cpp"] = encode(tu2_bytes)
            hashes["src/Bar.cpp"] = tu2_sha
            cache = root / "cache"
            self.assertTrue(base_cache.store(cache, row, plan, job, tools, hashes))
            plan2 = dict(plan, request_paths=["src/Foo.cpp", "src/Bar.cpp"], compile={"base": [row, row2]})
            compiled = []
            def fake_measure(git, judge, side, mplan, mtools, mjob, timing=None):
                (mjob / "obj").mkdir(parents=True)
                for tu in mplan["request_paths"]:
                    compiled.append(tu)
                    (mjob / "obj" / (tu.replace("/", "_") + ".obj")).write_bytes(make_coff(b"bar"))
                return {tu: {"rows": [], "gates": [], "object_verified": True} for tu in mplan["request_paths"]}
            class FakeJudge:
                def effective_source(self, name, raw): return raw
                def ledger(self, mjob): return {}
                def judge_tu(self, mjob, tu, ledger): return {"rows": [{"rva": "0x1", "status": "MATCH"}], "gates": [], "object_verified": True}
            with mock.patch.object(base_cache, "projection", return_value=(sources, hashes)), \
                 mock.patch.object(base_cache, "CONFIG", ()), \
                 mock.patch.object(base_cache, "data_entry"):
                res = base_cache.measure_base_with_cache(None, FakeJudge(), plan2, tools, root / "job_p", cache, measure_fn=fake_measure)
            self.assertEqual(compiled, ["src/Bar.cpp"])
            self.assertEqual(list(res), ["src/Foo.cpp", "src/Bar.cpp"])


if __name__ == "__main__":
    unittest.main()
