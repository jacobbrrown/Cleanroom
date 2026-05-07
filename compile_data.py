#!/usr/bin/env python3
"""
compile_data.py  —  Cleanroom Hub JSON compiler
================================================
Merges multiple exported JSON files into one, deduplicating by record ID.
The newest version of any record (by export timestamp) wins on conflict.

Usage:
    python3 compile_data.py                        # merges all .json files in current folder
    python3 compile_data.py *.json                 # explicit list
    python3 compile_data.py exports/ -o merged.json  # specify folder and output name

Output:
    cleanroom_merged.json   (or whatever -o specifies)

Then bake into HTML:
    python3 merge_data.py cleanroom_hub.html cleanroom_merged.json
"""

import sys, json, glob, argparse
from pathlib import Path

KEYS = ["runs", "rates", "notices", "recipes"]

def load_files(paths):
    files = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            found = sorted(path.glob("*.json"))
            print(f"  Folder {path}: found {len(found)} JSON file(s)")
            for f in found:
                files.append(f)
        else:
            files.append(path)
    return files

def parse_args():
    parser = argparse.ArgumentParser(description="Merge Cleanroom Hub JSON exports.")
    parser.add_argument("inputs", nargs="*", help="JSON files or folders (default: all .json in current folder)")
    parser.add_argument("-o", "--output", default="cleanroom_merged.json", help="Output filename")
    return parser.parse_args()

def main():
    args = parse_args()

    # Resolve input files
    if args.inputs:
        raw = []
        for inp in args.inputs:
            raw.extend(glob.glob(inp)) if '*' in inp else raw.append(inp)
        file_paths = load_files(raw)
    else:
        file_paths = sorted(Path(".").glob("cleanroom_data_*.json"))
        print(f"No inputs specified — scanning current folder for cleanroom_data_*.json")
        print(f"  Found {len(file_paths)} file(s)")

    if not file_paths:
        print("Error: no JSON files found.")
        sys.exit(1)

    # Load all files, sorted oldest-first so newer files overwrite on conflict
    exports = []
    for path in sorted(file_paths):
        path = Path(path)
        if not path.exists():
            print(f"  Warning: {path} not found, skipping")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  Warning: {path} is not valid JSON ({e}), skipping")
            continue
        # Validate it's a cleanroom export
        if not all(k in data for k in KEYS):
            print(f"  Warning: {path} missing expected keys, skipping")
            continue
        exports.append((path, data))
        print(f"  Loaded {path.name}  (exported: {data.get('exported','unknown')})")

    if not exports:
        print("Error: no valid cleanroom export files found.")
        sys.exit(1)

    # Merge — deduplicate by id, newest export timestamp wins
    merged = {key: {} for key in KEYS}  # key -> {id: record}

    for path, data in exports:
        for key in KEYS:
            for record in data.get(key, []):
                rid = record.get("id")
                if rid is None:
                    print(f"  Warning: record in {path.name}/{key} has no id, skipping")
                    continue
                merged[key][rid] = record  # later file overwrites earlier

    # Build output
    totals = {key: len(merged[key]) for key in KEYS}
    output = {
        "exported": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "compiled_from": [str(p) for p, _ in exports],
        **{key: list(merged[key].values()) for key in KEYS}
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"Merged {len(exports)} file(s):")
    for key in KEYS:
        print(f"  {key}: {totals[key]} unique record(s)")
    print(f"\nOutput: {out_path.resolve()}")
    print(f"Next:   python3 merge_data.py cleanroom_hub.html {out_path}")

if __name__ == "__main__":
    main()
