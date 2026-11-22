"""Select the highest attempt (<= max_attempt) per shard index from downloaded artifacts."""
import argparse
from pathlib import Path
import re
import shutil
import sys


def select(src, dst, prefix, max_attempt, expected):
    pattern = re.compile(rf"^{re.escape(prefix)}([0-9]+)-a([1-9][0-9]*)\Z")
    winners = {}
    src_path, dst_path = Path(src), Path(dst)
    dst_path.mkdir(parents=True, exist_ok=True)
    if src_path.is_dir():
        for entry in sorted(src_path.iterdir()):
            if not entry.is_dir() or entry.is_symlink():
                continue
            m = pattern.fullmatch(entry.name)
            if not m:
                continue
            shard, attempt = int(m.group(1)), int(m.group(2))
            if not (0 <= shard < expected and 1 <= attempt <= max_attempt):
                continue
            if shard not in winners or attempt > winners[shard][0]:
                winners[shard] = (attempt, entry)
    reused = 0
    for shard, (attempt, entry) in sorted(winners.items()):
        if attempt < max_attempt:
            reused += 1
        target = dst_path / f"{prefix}{shard}-a{attempt}"
        if not target.exists():
            shutil.move(str(entry), str(target))
    print(f"Selected {len(winners)}/{expected} {prefix}* shards (reused {reused} from earlier attempts).")
    return winners


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--dst", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--max-attempt", type=int, required=True)
    parser.add_argument("--expected", type=int, required=True)
    args = parser.parse_args()
    select(args.src, args.dst, args.prefix, args.max_attempt, args.expected)


if __name__ == "__main__":
    sys.exit(main())
