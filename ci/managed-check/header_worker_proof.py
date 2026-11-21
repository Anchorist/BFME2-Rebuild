"""Adapt isolated compiler results to protected H2/H5 evidence."""


from header_decl_check import GIT_ID, SHA256, canonical_header, sha256
from pool_protocol import MAX_FILE, MAX_OBJECT, VERSION, check_object, decode, encode, pack_sources
from pool_worker import MAX_HEADERS, MAX_PLAN, MAX_REQUEST, json_bytes
from pool_compare import TrustedPaths


def plan(requests, tree, sources, hashes, *, profile, compiler, debug=False):
    """Prepare up to eight synthetic probes without changing the Git source projection.

    Each request is made by protected policy after inventorying the exact changed
    header. Source and includes come from the protected plan, never a PR artifact.
    The resulting compiler command has fixed settings and never links or runs a TU.
    """
    if not (GIT_ID.fullmatch(tree) and SHA256.fullmatch(profile) and SHA256.fullmatch(compiler)):
        raise ValueError("Incorrect header probe input identity")
    if not 0 < len(requests) <= MAX_PLAN:
        raise ValueError("Invalid header probe batch size")
    sources = dict(sources)
    hashes = dict(hashes)
    rows, contracts = [], {}
    folded = {p.casefold() for p in sources}
    for header, probe_bytes, source_context in requests:
        header = canonical_header(header)
        if header not in hashes or header not in sources or not 0 < len(probe_bytes) <= MAX_FILE:
            raise ValueError("Missing header or invalid probe source")
        if header in source_context or len(source_context) != len(set(source_context)):
            raise ValueError("Repeated protected header context")
        for path in source_context:
            canonical_header(path)
            if path not in hashes or path not in sources:
                raise ValueError("Missing protected header context")
        fixed = b"".join(
            ('#include "' + path.removeprefix("include/") + '"\n').encode("ascii")
            for path in source_context
        )
        if fixed:
            probe_bytes = fixed + probe_bytes
        source = sha256(probe_bytes)
        path = "src/managed-header-probe_" + sha256(json_bytes([header, source])) + ".cpp"
        if path.casefold() in folded:
            raise ValueError("A protected header probe name collides with source")
        folded.add(path.casefold())
        sources[path], hashes[path] = encode(probe_bytes), source
        flags = ["-nologo", "-c", "-Od", "-DNDEBUG", "-MD", "-EHsc", "-showIncludes",
                 "-D_STLP_USE_STATIC_LIB", "-D_STLP_USE_MALLOC", "-D_BFME_RETAIL_TREE_INSERT_LAYOUT",
                 "-I@overlay/base", "-I@stlport46/stlport", "-Iinclude"]
        if debug:
            flags.append("-Z7")
        env = {"INCLUDE": ["vc/Vc7/include"],
               "WINEPATH": ["vc/Vc7/bin", "vc/Common7/IDE", "vcruntime"],
               "LANG": "C", "LC_ALL": "C", "WINEDEBUG": "-all"}
        pins = {"tree": tree, "profile_sha256": profile, "compiler_sha256": compiler,
                "probe_sha256": source, "header_sha256": hashes[header]}
        contract = sha256(json_bytes({"pins": pins, "flags": flags, "env": env,
                                     "header": header, "context": list(source_context)}))
        rows.append({"tu": path, "source": source, "contract": contract, "flags": flags, "env": env})
        contracts[path] = header, pins, tuple(source_context)
    wire = json_bytes({"version": VERSION, "profile": profile, "source": pack_sources(sources), "plan": rows})
    if len(wire) > MAX_REQUEST:
        raise ValueError("Header probe request exceeds compiler size policy")
    return wire, rows, contracts, hashes


def collect(reply, payload, rows, contracts, hashes, roots):
    """Require exact findings from the already audited sealed compiler launcher."""
    found = reply.get("results")
    if (reply.get("version") != VERSION or reply.get("request") != sha256(payload)
            or reply.get("profile") != next(iter(contracts.values()))[1]["profile_sha256"]
            or not isinstance(found, list) or len(found) != len(rows)):
        raise ValueError("Compiler response differs from the header probe request")
    paths = TrustedPaths(roots, hashes)
    result = {}
    for row, observed in zip(rows, found, strict=True):
        if any(observed.get(k) != row[k] for k in ("tu", "source", "contract")):
            raise ValueError("Compiler response differs from the probe identity")
        tu = row["tu"]
        header, pins, context = contracts[tu]
        exact = {"tu", "source", "contract", "status"}
        if observed.get("status") == "error" and set(observed) == exact | {"diagnostics"}:
            result[tu] = {"status": "held", "header": header, "reason": "isolated probe did not compile"}
            continue
        if observed.get("status") != "compiled" or set(observed) != exact | {"artifact", "sha256", "includes"}:
            raise ValueError("Unsupported header probe response")
        obj = decode(observed["artifact"], MAX_OBJECT)
        if check_object(obj) != observed["sha256"]:
            raise ValueError("Compiler probe object differs from its receipt")
        includes = observed["includes"]
        if not isinstance(includes, list) or len(includes) > MAX_HEADERS:
            raise ValueError("Invalid header probe includes")
        verified = [paths.dependency(item) for item in includes]
        if len(set(verified)) != len(verified):
            raise ValueError("Repeated compiler probe dependency")
        input_hashes = {path: hashes[path] for role, path in verified if role == "source"}
        for name in (header, *context):
            if input_hashes.get(name) != hashes[name]:
                raise ValueError(f"Header probe did not bind mandatory source: {name}")
        receipt = {**{k: v for k, v in pins.items() if k != "header_sha256"},
                   "exit": 0, "input_sha256": input_hashes, "object_sha256": sha256(obj),
                   "compiler_request_sha256": reply["request"], "compiler_contract": row["contract"]}
        result[tu] = {"status": "observed", "header": header,
                      "pins": pins, "receipt": receipt, "object": obj}
    return result
