"""Project private native measurements into the compact main state schema."""
import hashlib
from state_snapshot import unit_status


def compact(raw, units, *, prehashed=False):
    if not isinstance(raw, dict) or set(raw) != {"binding", "results"} or not isinstance(raw["results"], list):
        raise ValueError("The installed comparator did not return a bound result.")
    checks = {}
    for result in raw["results"]:
        name = result["tu"]
        rows, proof = {}, []
        if name in checks:
            raise ValueError("The comparator repeated a translation unit.")
        for row in result["rows"]:
            key, status = row["rva"], row["status"]
            if key in rows:
                raise ValueError("The comparator repeated a function row.")
            rows[key] = [status, row.get("pct", 100 if status == "MATCH" else 0)]
            if row.get("credited") is True and row.get("proof") == "proven":
                proof.append(key)
        raw_gates = result["gates"]
        if (not isinstance(raw_gates, list) or len(raw_gates) > 512
                or not all(isinstance(g, str) and g and len(g) <= 2048 for g in raw_gates)):
            raise ValueError("The native checker returned invalid gate diagnostics.")
        gates = sorted({g.rsplit(" ", 1)[-1] if prehashed else hashlib.sha256(g.encode("utf-8")).hexdigest()
                        for g in raw_gates})
        checks[name] = unit_status({"rows": rows, "proven": proof, "gate_sha256": gates,
                                    "verified": result["object_verified"], "error": bool(result.get("error"))})
    if set(checks) != set(units):
        raise ValueError("The installed comparator did not measure every assigned translation unit.")
    return checks

