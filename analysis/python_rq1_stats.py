#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RQ1 statistics for the *Python* replication of the Stack Overflow answer-edit study.

Reproduces, for Python, the numbers reported in the Java RQ1 paragraph:
  - number of accepted answers                         (baseline denominator)
  - number of code snippets + avg/std per answer       (latest version)
  - number of answers with >= 1 revision + percentage  (the filtered set)
  - average / median / max revisions per answer
  - total code snippets across all revisions
  - the answer with the most revisions (+ its date span)
  - a revisions-distribution histogram (post_revisions_histogram.pdf)

The filtered set is read from the answer-id file produced by extract_answer_list.py.
Baseline figures are computed over *all* accepted answers for the tag.

Dependency:
    pip install mysql-connector-python matplotlib

Example:
    python python_rq1_stats.py
    python python_rq1_stats.py --tag python --skip-baseline
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

try:
    import mysql.connector
except ImportError:
    sys.exit("Missing dependency: pip install mysql-connector-python")

REPO_ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = Path(__file__).resolve().parent
DEFAULT_ANSWER_LIST = REPO_ROOT / "files" / "acceptedWithVersionAnswer_python.txt"

INSERT_BATCH = 20_000


def log(msg):
    print(msg, flush=True)


def resolve_tag_id(cursor, tag_name):
    cursor.execute("SELECT Id, Count FROM Tags WHERE TagName = %s", (tag_name,))
    row = cursor.fetchone()
    if row is None:
        sys.exit(f"Tag '{tag_name}' not found in the Tags table.")
    log(f"Tag '{tag_name}' -> TagId {row[0]} ({row[1]:,} questions)")
    return row[0]


def compute_baseline(cursor, tag_id):
    """All accepted answers for the tag: count + latest-version code-snippet stats."""
    log("\n[baseline] materializing all accepted answers for the tag...")
    t0 = time.perf_counter()
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS _rq1_all_accepted")
    cursor.execute("CREATE TEMPORARY TABLE _rq1_all_accepted (Id INT PRIMARY KEY)")
    cursor.execute(
        """
        INSERT IGNORE INTO _rq1_all_accepted (Id)
        SELECT q.AcceptedAnswerId
        FROM Posts q
        JOIN PostTags pt ON pt.PostId = q.Id AND pt.TagId = %s
        WHERE q.PostTypeId = 1 AND q.AcceptedAnswerId IS NOT NULL
        """,
        (tag_id,),
    )
    cursor.execute("SELECT COUNT(*) FROM _rq1_all_accepted")
    total_accepted = cursor.fetchone()[0]
    log(f"[baseline] accepted answers: {total_accepted:,}  ({time.perf_counter() - t0:.0f}s)")

    log("[baseline] counting latest-version code snippets per answer (may take minutes)...")
    t0 = time.perf_counter()
    cursor.execute(
        """
        SELECT COUNT(*)          AS answers,
               COALESCE(SUM(cnt), 0) AS snippets,
               AVG(cnt)          AS avg_snippets,
               STDDEV_SAMP(cnt)  AS std_snippets
        FROM (
            SELECT aa.Id, COUNT(pbv.Id) AS cnt
            FROM _rq1_all_accepted aa
            LEFT JOIN PostBlockVersion pbv
                   ON pbv.PostId = aa.Id
                  AND pbv.PostBlockTypeId = 2
                  AND pbv.MostRecentVersion = 1
            GROUP BY aa.Id
        ) x
        """
    )
    _, snippets, avg_snip, std_snip = cursor.fetchone()
    log(f"[baseline] code snippets: {int(snippets):,}  "
        f"avg {float(avg_snip):.2f}/answer, std {float(std_snip):.2f}  "
        f"({time.perf_counter() - t0:.0f}s)")
    return {
        "total_accepted": total_accepted,
        "total_snippets": int(snippets),
        "avg_snippets": float(avg_snip),
        "std_snippets": float(std_snip),
    }


def load_filtered_ids(cursor, answer_list):
    """Load the filtered answer ids from the list file into a temporary table."""
    if not answer_list.exists():
        sys.exit(f"Answer list not found: {answer_list}\n"
                 f"Run extract_answer_list.py first.")
    ids = [int(line) for line in answer_list.read_text().split() if line.strip()]
    log(f"\n[filtered] loading {len(ids):,} answer ids from {answer_list.name}...")
    cursor.execute("DROP TEMPORARY TABLE IF EXISTS _rq1_filtered")
    cursor.execute("CREATE TEMPORARY TABLE _rq1_filtered (Id INT PRIMARY KEY)")
    for i in range(0, len(ids), INSERT_BATCH):
        batch = ids[i:i + INSERT_BATCH]
        cursor.executemany("INSERT IGNORE INTO _rq1_filtered (Id) VALUES (%s)",
                           [(x,) for x in batch])
    return len(ids)


def compute_filtered(cursor):
    """Revision counts, snippet-across-revisions count, and the most-revised answer."""
    log("[filtered] counting versions per answer...")
    cursor.execute(
        """
        SELECT pv.PostId, COUNT(*) AS versions
        FROM PostVersion pv
        JOIN _rq1_filtered t ON t.Id = pv.PostId
        GROUP BY pv.PostId
        """
    )
    counts = {}
    for post_id, versions in cursor.fetchall():
        counts[post_id] = versions
    revisions = list(counts.values())

    log("[filtered] counting code snippets across all revisions...")
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM PostBlockVersion pbv
        JOIN _rq1_filtered t ON t.Id = pbv.PostId
        WHERE pbv.PostBlockTypeId = 2
        """
    )
    snippets_all_revisions = cursor.fetchone()[0]

    # most-revised answer + its date span
    most_revised_id = max(counts, key=counts.get)
    cursor.execute(
        "SELECT MIN(CreationDate), MAX(CreationDate) FROM PostVersion WHERE PostId = %s",
        (most_revised_id,),
    )
    first_date, last_date = cursor.fetchone()

    return {
        "revisions": revisions,
        "counts": counts,
        "snippets_all_revisions": snippets_all_revisions,
        "most_revised_id": most_revised_id,
        "most_revised_count": counts[most_revised_id],
        "most_revised_first": first_date,
        "most_revised_last": last_date,
    }


def draw_histogram(revisions, output_path):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        log("matplotlib not installed; skipping histogram (pip install matplotlib)")
        return
    max_rev = max(revisions)
    bins = range(min(revisions), max_rev + 2)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(revisions, bins=bins, color="#4d4d4d", edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Number of revisions", fontsize=14)
    ax.set_ylabel("Number of answers", fontsize=14)
    ax.set_yscale("log")
    ax.tick_params(axis="both", which="major", labelsize=12)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight", format="pdf")
    plt.close(fig)
    log(f"Histogram saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default="")
    parser.add_argument("--database", default="sotorrent")
    parser.add_argument("--tag", default="python")
    parser.add_argument("--answer-list", type=Path, default=DEFAULT_ANSWER_LIST,
                        help="Filtered answer-id file from extract_answer_list.py")
    parser.add_argument("--hist-output", type=Path,
                        default=ANALYSIS_DIR / "post_revisions_histogram.pdf")
    parser.add_argument("--skip-baseline", action="store_true",
                        help="Skip the slow all-accepted-answers baseline queries")
    args = parser.parse_args()

    db = mysql.connector.connect(host=args.host, user=args.user,
                                 password=args.password, database=args.database)
    try:
        cursor = db.cursor()
        tag_id = resolve_tag_id(cursor, args.tag)

        baseline = None if args.skip_baseline else compute_baseline(cursor, tag_id)

        filtered_total = load_filtered_ids(cursor, args.answer_list)
        f = compute_filtered(cursor)
        db.commit()
        cursor.close()
    finally:
        db.close()

    revisions = f["revisions"]
    draw_histogram(revisions, args.hist_output)

    # ---- RQ1 summary ----
    print("\n" + "=" * 70)
    print(f"RQ1 STATISTICS - tag '{args.tag}'")
    print("=" * 70)
    if baseline:
        pct = 100.0 * filtered_total / baseline["total_accepted"]
        print(f"Accepted answers:                 {baseline['total_accepted']:,}")
        print(f"Code snippets (latest version):   {baseline['total_snippets']:,}")
        print(f"  avg per answer:                 {baseline['avg_snippets']:.2f}")
        print(f"  std:                            {baseline['std_snippets']:.2f}")
        print(f"Answers with >= 1 revision:       {filtered_total:,} ({pct:.2f}%)")
    else:
        print(f"Answers with >= 1 revision:       {filtered_total:,} "
              f"(baseline skipped -> no percentage)")
    print(f"Avg revisions per answer:         {statistics.mean(revisions):.2f}")
    print(f"Median revisions per answer:      {statistics.median(revisions):.1f}")
    print(f"Std revisions per answer:         {statistics.pstdev(revisions):.2f}")
    print(f"Max revisions:                    {f['most_revised_count']} "
          f"(post ID {f['most_revised_id']})")
    print(f"  first revision:                 {f['most_revised_first']}")
    print(f"  last revision:                  {f['most_revised_last']}")
    print(f"Code snippets across all revs:    {f['snippets_all_revisions']:,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
