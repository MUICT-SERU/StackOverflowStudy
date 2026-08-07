#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descriptive statistics of the Stack Overflow code edit sizes, for the RQ1 stage.

The RQ1 notebooks report the headline Levenshtein figures (count, min, max, mean, median,
standard deviation) via code_diff.print_statistics. This script derives the rest of the
distribution reported in the technical report, which the notebooks do not compute:

  - the proportion of code blocks that are byte-identical between the original and the
    latest revision, i.e. blocks whose answer was edited but whose code was not
  - the distribution restricted to the blocks that actually changed
  - selected quantiles of the full distribution
  - per-answer aggregates: answers with at least one original/recent pair, the average
    number of code blocks per edited answer, and how many answers contain at least one
    block that changed, both as a share of edited answers and of all accepted answers

Input is the distance CSV written by the RQ1 stage, whose rows are

    <path>/{PostId}_{LocalId}_original.{ext},<path>/{PostId}_{LocalId}_recent.{ext},<distance>

The two CSVs differ in whether the paths are relative or absolute, so the PostId is taken
from the parent directory name, which is the PostId in both layouts.

The accepted-answer totals below are the denominators reported by the RQ1 notebooks, which
compute them from SOTorrent. They are recorded here so that the percentages this script
prints are reproducible without a database connection; override them with --accepted if
the underlying dataset changes.

Example:
    python levenshtein_stats.py
    python levenshtein_stats.py --lang python --json levenshtein_stats.json
"""

import argparse
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ANALYSIS_DIR = Path(__file__).resolve().parent

LANGS = {
    "python": {
        "csv": ANALYSIS_DIR / "levenshtein_distances_python.csv",
        # Accepted answers carrying the tag, from python_rq1_stats.ipynb.
        "accepted_answers": 840_132,
    },
    "javascript": {
        "csv": ANALYSIS_DIR / "levenshtein_distances_javascript.csv",
        # Accepted answers carrying the tag, from javascript_rq1_stats.ipynb.
        "accepted_answers": 1_144_185,
    },
}

QUANTILES = (0.25, 0.50, 0.75, 0.90, 0.95, 0.99)


def quantile(sorted_values, p):
    """Nearest-rank quantile, matching the figures quoted in the technical report."""
    if not sorted_values:
        return None
    return sorted_values[int(p * (len(sorted_values) - 1))]


def analyse(lang, cfg, accepted_answers):
    path = cfg["csv"]
    if not path.exists():
        sys.exit(f"Missing distance CSV: {path}\n"
                 f"Run the RQ1 stage with RUN_DISTANCE_COMPUTATION = True first.")

    print(f"\n=== {lang} ===")
    print(f"reading {path.name}...")

    distances = []
    blocks_per_post = defaultdict(int)
    changed_per_post = defaultdict(int)

    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # header
        for row in reader:
            if len(row) < 3:
                continue
            distance = int(row[2])
            distances.append(distance)
            # The parent directory is the PostId under both the relative and the
            # absolute path layouts used by the two CSVs.
            post_id = Path(row[0]).parent.name
            blocks_per_post[post_id] += 1
            if distance > 0:
                changed_per_post[post_id] += 1

    distances.sort()
    total = len(distances)
    changed = [d for d in distances if d > 0]
    zeros = total - len(changed)

    posts = len(blocks_per_post)
    posts_changed = len(changed_per_post)

    result = {
        "language": lang,
        "accepted_answers": accepted_answers,
        "pairs": total,
        "min": distances[0],
        "max": distances[-1],
        "mean": statistics.mean(distances),
        "median": statistics.median(distances),
        "std": statistics.stdev(distances),
        "quantiles": {f"p{int(p * 100)}": quantile(distances, p) for p in QUANTILES},
        "unchanged_pairs": zeros,
        "unchanged_pct": 100.0 * zeros / total,
        "changed_pairs": len(changed),
        "changed_pct": 100.0 * len(changed) / total,
        "changed_mean": statistics.mean(changed) if changed else 0.0,
        "changed_median": statistics.median(changed) if changed else 0.0,
        "answers_with_pairs": posts,
        "blocks_per_answer": total / posts if posts else 0.0,
        "answers_with_changed_block": posts_changed,
        "answers_with_changed_block_pct_of_edited": 100.0 * posts_changed / posts if posts else 0.0,
        "answers_with_changed_block_pct_of_accepted": 100.0 * posts_changed / accepted_answers,
    }
    return result


def print_result(r):
    print(f"\n  Full distribution ({r['pairs']:,} original/recent pairs)")
    print(f"    min {r['min']:,}   max {r['max']:,}   "
          f"mean {r['mean']:.2f}   median {r['median']:.0f}   std {r['std']:.2f}")
    q = r["quantiles"]
    print("    quantiles  " + "   ".join(f"{k} {v:,}" for k, v in q.items()))

    print("\n  Unchanged versus changed blocks")
    print(f"    unchanged  {r['unchanged_pairs']:>9,}  ({r['unchanged_pct']:.2f}%)")
    print(f"    changed    {r['changed_pairs']:>9,}  ({r['changed_pct']:.2f}%)")
    print(f"    changed-only mean {r['changed_mean']:.2f}, "
          f"median {r['changed_median']:.0f}")

    print("\n  Per answer")
    print(f"    answers with at least one pair          {r['answers_with_pairs']:>9,}")
    print(f"    average code blocks per edited answer   {r['blocks_per_answer']:>9.2f}")
    print(f"    answers with at least one changed block {r['answers_with_changed_block']:>9,}")
    print(f"      as a share of edited answers          "
          f"{r['answers_with_changed_block_pct_of_edited']:>9.2f}%")
    print(f"      as a share of accepted answers        "
          f"{r['answers_with_changed_block_pct_of_accepted']:>9.2f}%")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lang", choices=sorted(LANGS), action="append",
                        help="Language to analyse, repeatable (default: all)")
    parser.add_argument("--accepted", type=int,
                        help="Override the accepted-answer denominator "
                             "(only meaningful with a single --lang)")
    parser.add_argument("--json", type=Path, help="Write the results to JSON")
    args = parser.parse_args()

    langs = args.lang or sorted(LANGS)
    if args.accepted is not None and len(langs) != 1:
        sys.exit("--accepted requires exactly one --lang")

    results = {}
    for lang in langs:
        accepted = args.accepted or LANGS[lang]["accepted_answers"]
        result = analyse(lang, LANGS[lang], accepted)
        print_result(result)
        results[lang] = result

    if args.json:
        args.json.write_text(json.dumps(results, indent=2))
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
