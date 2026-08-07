#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aggregate the Matcha (Siamese+) clone-search results by GitHub project popularity group.

This is the RQ2 stage of the Python and JavaScript replication. Unlike the Java study it
performs no manual classification, so it reports how many Stack Overflow answer edits were
matched in each project group, not what kind of improvement each edit represents.

Inputs, all under analysis/so-gh_clones/:

  {lang}_repos_stars10-25_forks0-14.txt      low-popularity project URLs
  {lang}_repos_stars26-271_forks15-105.txt   medium-popularity project URLs
  {lang}_repos_stars272plus_forks106plus.txt high-popularity project URLs
  search_results_{python_new,js}/{repo}_{timestamp}.csv   one result file per project

Each result line is headerless and comma separated:

  <project method>,<matched SO snippet>,<matched SO snippet>,...

where a project method is

  /path/to/repo/file.py_<methodName>#<startLine>#<endLine>

and a matched SO snippet is

  <PostId>/<PostId>_<LocalId>_<revision>.py_<methodName>#<startLine>#<endLine>

with <revision> being a PostHistoryId, or the literal "original" or "recent". Because the
Matcha index holds every revision of every code block, one project method typically
matches several revisions of the same block; those are folded together here.

The unit of interest is the Stack Overflow *answer edit*, identified by the code block
(PostId, LocalId). A block only counts as an edit when its content actually changed
between the original and the latest revision, which is checked against the Levenshtein
distance CSV produced by the RQ1 stage. Blocks whose distance is 0 were matched but never
edited, so they carry no improvement to recommend and are reported separately.

Example:
    python aggregate_so_gh_clones.py
    python aggregate_so_gh_clones.py --lang python --json out.json
"""

import argparse
import csv
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ANALYSIS_DIR = Path(__file__).resolve().parent
CLONES_DIR = ANALYSIS_DIR / "so-gh_clones"

GROUPS = ("low", "medium", "high")

LANGS = {
    "python": {
        "results_dir": "search_results_python_new",
        "repo_lists": {
            "low": "python_repos_stars10-25_forks0-14.txt",
            "medium": "python_repos_stars26-271_forks15-105.txt",
            "high": "python_repos_stars272plus_forks106plus.txt",
        },
        "distances": ANALYSIS_DIR / "levenshtein_distances_python.csv",
        "extension": "py",
    },
    "javascript": {
        "results_dir": "search_results_js",
        "repo_lists": {
            "low": "javascript_repos_stars10-25_forks0-14.txt",
            "medium": "javascript_repos_stars26-271_forks15-105.txt",
            "high": "javascript_repos_stars272plus_forks106plus.txt",
        },
        "distances": ANALYSIS_DIR / "levenshtein_distances_javascript.csv",
        "extension": "js",
    },
}

TIMESTAMP_RE = re.compile(r"_\d{8}_\d{6}\.csv$")
# <PostId>/<PostId>_<LocalId>_<revision>.<ext>_<method>#<start>#<end>
MATCH_RE = re.compile(r"(?:^|/)(\d+)_(\d+)_([A-Za-z0-9]+)\.[A-Za-z]+_")


def repo_name(url):
    """Last path component of a GitHub URL, which is how result files are named."""
    return url.rstrip("/").split("/")[-1]


def load_groups(cfg):
    """Map repository name -> popularity group."""
    group_of = {}
    counts = {}
    for group in GROUPS:
        path = CLONES_DIR / cfg["repo_lists"][group]
        if not path.exists():
            sys.exit(f"Missing repository list: {path}")
        names = [repo_name(line) for line in path.read_text().split() if line.strip()]
        for name in names:
            if name in group_of:
                print(f"  warning: {name} appears in more than one group "
                      f"({group_of[name]} and {group}), keeping {group_of[name]}")
                continue
            group_of[name] = group
        counts[group] = len(names)
    return group_of, counts


def load_edited_blocks(distance_csv):
    """Return (edited, seen) sets of (PostId, LocalId).

    edited holds the blocks whose original and latest revisions differ, i.e. the blocks
    that carry an actual Stack Overflow answer edit. seen holds every block for which a
    distance was computed, so that blocks absent from the CSV can be reported as unknown
    rather than silently treated as unedited.
    """
    if not distance_csv.exists():
        print(f"  warning: {distance_csv.name} not found, "
              f"edited-block filtering disabled")
        return None, None

    edited, seen = set(), set()
    with open(distance_csv, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # header
        for row in reader:
            if len(row) < 3:
                continue
            stem = Path(row[0]).name  # {PostId}_{LocalId}_original.{ext}
            parts = stem.split("_")
            if len(parts) < 3:
                continue
            key = (parts[0], parts[1])
            seen.add(key)
            if int(row[2]) > 0:
                edited.add(key)
    return edited, seen


def parse_result_file(path):
    """Yield (project_method, [(PostId, LocalId, revision), ...]) per result line."""
    with open(path, newline="", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            fields = line.split(",")
            blocks = []
            for field in fields[1:]:
                m = MATCH_RE.search(field)
                if m:
                    blocks.append((m.group(1), m.group(2), m.group(3)))
            if blocks:
                yield fields[0], blocks


def analyse(lang, cfg):
    print(f"\n=== {lang} ===")
    results_dir = CLONES_DIR / cfg["results_dir"]
    if not results_dir.is_dir():
        sys.exit(f"Missing results directory: {results_dir}")

    group_of, project_counts = load_groups(cfg)
    edited, seen = load_edited_blocks(cfg["distances"])

    # per group aggregates
    matched_lines = defaultdict(int)              # candidate clone pairs
    blocks = defaultdict(set)                     # (PostId, LocalId) matched
    edited_blocks = defaultdict(set)              # ... restricted to genuine edits
    answers = defaultdict(set)                    # distinct PostIds
    edited_answers = defaultdict(set)
    per_project_edits = defaultdict(dict)         # group -> repo -> edited block count
    projects_with_hits = defaultdict(int)
    unknown_blocks = set()

    unmatched_files = []
    for path in sorted(results_dir.glob("*.csv")):
        name = TIMESTAMP_RE.sub("", path.name)
        group = group_of.get(name)
        if group is None:
            unmatched_files.append(path.name)
            continue

        repo_blocks, repo_edited = set(), set()
        lines = 0
        for _, matches in parse_result_file(path):
            lines += 1
            for post_id, local_id, _rev in matches:
                key = (post_id, local_id)
                repo_blocks.add(key)
                if edited is None:
                    repo_edited.add(key)
                elif key in edited:
                    repo_edited.add(key)
                elif seen is not None and key not in seen:
                    unknown_blocks.add(key)

        matched_lines[group] += lines
        blocks[group] |= repo_blocks
        edited_blocks[group] |= repo_edited
        answers[group] |= {b[0] for b in repo_blocks}
        edited_answers[group] |= {b[0] for b in repo_edited}
        per_project_edits[group][name] = len(repo_edited)
        if lines:
            projects_with_hits[group] += 1

    if unmatched_files:
        print(f"  warning: {len(unmatched_files)} result files not in any repository list: "
              f"{unmatched_files[:5]}")
    if unknown_blocks:
        print(f"  note: {len(unknown_blocks):,} matched blocks have no Levenshtein entry "
              f"and are excluded from the edited counts")

    summary = {"language": lang, "groups": {}}
    for group in GROUPS:
        per_project = [per_project_edits[group].get(r, 0)
                       for r in per_project_edits[group]]
        summary["groups"][group] = {
            "projects": project_counts[group],
            "projects_with_matches": projects_with_hits[group],
            "candidate_pairs": matched_lines[group],
            "blocks_matched": len(blocks[group]),
            "answer_edits": len(edited_blocks[group]),
            "answers_matched": len(answers[group]),
            "answers_with_edits": len(edited_answers[group]),
            "max_edits_per_project": max(per_project) if per_project else 0,
            "avg_edits_per_project": (statistics.mean(per_project)
                                      if per_project else 0.0),
            "per_project": per_project_edits[group],
        }

    # totals across groups, de-duplicated: the same SO block can be matched in projects
    # belonging to different groups
    all_edited = set().union(*(edited_blocks[g] for g in GROUPS)) if GROUPS else set()
    all_blocks = set().union(*(blocks[g] for g in GROUPS)) if GROUPS else set()
    summary["total"] = {
        "projects": sum(project_counts.values()),
        "candidate_pairs": sum(matched_lines.values()),
        "blocks_matched_distinct": len(all_blocks),
        "answer_edits_distinct": len(all_edited),
    }
    return summary


def run_tests(summary):
    """Shapiro-Wilk then Kruskal-Wallis over per-project edit counts, as in the paper."""
    try:
        from scipy import stats
    except ImportError:
        print("\n  (scipy not installed, skipping the statistical tests)")
        return None

    samples = [list(summary["groups"][g]["per_project"].values()) for g in GROUPS]
    print("\n  Shapiro-Wilk normality test per group:")
    normal = True
    for group, sample in zip(GROUPS, samples):
        w, p = stats.shapiro(sample)
        normal &= p >= 0.05
        print(f"    {group:<8} n={len(sample):<4} W={w:.4f}  p={p:.3e}")
    print(f"  -> {'normal' if normal else 'non-normal'}, "
          f"{'parametric test would be admissible' if normal else 'using Kruskal-Wallis'}")

    h, p = stats.kruskal(*samples)
    print(f"\n  Kruskal-Wallis: H={h:.6f}  p={p:.6f}  df={len(GROUPS) - 1}")
    print(f"  -> {'reject' if p < 0.05 else 'retain'} H0 at alpha=0.05: "
          f"{'a' if p < 0.05 else 'no'} statistically significant difference "
          f"in answer edits across the project groups")

    print("\n  Pairwise Mann-Whitney U (uncorrected, exploratory):")
    for i in range(len(GROUPS)):
        for j in range(i + 1, len(GROUPS)):
            u, pu = stats.mannwhitneyu(samples[i], samples[j], alternative="two-sided")
            print(f"    {GROUPS[i]:<7} vs {GROUPS[j]:<7} U={u:>7.1f}  p={pu:.6f}")

    return {"kruskal_h": h, "kruskal_p": p}


def print_summary(summary):
    g = summary["groups"]
    print(f"\n  {'Group':<10}{'Projects':>9}{'w/ matches':>12}{'Pairs':>8}"
          f"{'Blocks':>9}{'Edits':>7}{'Max':>6}{'Avg':>9}")
    for group in GROUPS:
        r = g[group]
        print(f"  {group:<10}{r['projects']:>9}{r['projects_with_matches']:>12}"
              f"{r['candidate_pairs']:>8}{r['blocks_matched']:>9}"
              f"{r['answer_edits']:>7}{r['max_edits_per_project']:>6}"
              f"{r['avg_edits_per_project']:>9.4f}")
    t = summary["total"]
    print(f"  {'total':<10}{t['projects']:>9}{'':>12}{t['candidate_pairs']:>8}"
          f"{t['blocks_matched_distinct']:>9}{t['answer_edits_distinct']:>7}")
    print("\n  Pairs  = result lines with at least one match (candidate clone pairs)")
    print("  Blocks = distinct SO code blocks (PostId, LocalId) matched")
    print("  Edits  = blocks whose original and latest revisions differ")
    print("  Max/Avg are edits per project, over the projects in the group")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lang", choices=sorted(LANGS), action="append",
                        help="Language to analyse, repeatable (default: all)")
    parser.add_argument("--json", type=Path,
                        help="Write the full summary, including per-project counts, to JSON")
    args = parser.parse_args()

    langs = args.lang or sorted(LANGS)
    summaries = {}
    for lang in langs:
        summary = analyse(lang, LANGS[lang])
        print_summary(summary)
        tests = run_tests(summary)
        if tests:
            summary["tests"] = tests
        summaries[lang] = summary

    if args.json:
        args.json.write_text(json.dumps(summaries, indent=2))
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
