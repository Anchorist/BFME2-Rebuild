# Protected paired compilation on Boat

The managed check uses the audited bfme2-compiler-v1 image. The protected planner derives an exact base, contributor head and candidate tree, then computes the affected TU closure with the trusted native planner. Candidate Git data supplies source and headers. Policy, checker, compiler, reference baselines and expected results come from the protected base or immutable image.

- The protected plan binds every compile to its TU, source digest, portable flags, environment and native compiler contract. Deterministic largest-first assignment keeps both sides of each TU on one runner. Use measured costs where available.
- A matrix job accepts its own index and the complete plan SHA-256, compiles the exact assignment in the sealed child in batches of at most eight, and returns its separately checked dependency and COFF receipts plus native verdicts.
- The join accepts artifacts from the current trusted Actions run only. It rejects incomplete, duplicate, stale, foreign, and mismatched scope before emitting contributor verdicts. Keep the artifacts and source references private, and delete raw COFF when the approved receipt retention ends.
- Record event-to-verdict time, per-shard queue and execution time, and join time. Fifteen minutes is the measured threshold for the wide fixture.

An object's raw SHA-256 binds one exact compiler artifact. Independent runs can change COFF FileHeader.TimeDateStamp and the temporary job path recorded in .debug$S. The native comparison evaluates declared code, relocations, data obligations, proof and object symbols. It ignores those volatile header and debug fields during verdict computation, without rewriting them. Six retained P26 pairs showed those were the only varying bytes in the sample.
