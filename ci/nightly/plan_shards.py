"""Deterministic split of the source files of one commit across compile shards (largest first, least loaded)."""


def source_files(git, sha):
    """{path: blob size} for every src/**/*.c and *.cpp at sha."""
    out = {}
    for line in git.value("ls-tree", "-r", "-l", sha, "--", "src").splitlines():
        meta, path = line.split("\t", 1)
        kind, size = meta.split()[1], meta.split()[3]
        if kind == "blob" and path.endswith((".cpp", ".c")):
            out[path] = int(size)
    return out


def assign(sizes, shards):
    """Same input, same output: a list of `shards` sorted path lists, balanced by total size."""
    if shards < 1:
        raise ValueError("at least one shard is required")
    load = [0] * shards
    groups = [[] for _ in range(shards)]
    for path, size in sorted(sizes.items(), key=lambda kv: (-kv[1], kv[0])):
        i = min(range(shards), key=lambda k: (load[k], k))
        groups[i].append(path)
        load[i] += max(size, 1)
    return [sorted(g) for g in groups]
