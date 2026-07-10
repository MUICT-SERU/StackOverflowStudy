#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the list of accepted answers (for a given tag) that contain revisions.

This is the language-configurable analog of files/acceptedWithVersionAnswer.txt:
it produces one Stack Overflow answer Id per line, which the Java stage
(SOTorrentAnalyzer/PostBlockProcessor.java) reads as its input.

An answer is included when, in the SOTorrent database, it is:
  1. Accepted  -> its Id equals its parent question's AcceptedAnswerId
  2. Tagged    -> the parent question carries the requested tag (default: python)
  3. Revised   -> it has a PostVersion row with a predecessor
                  (PredPostHistoryId IS NOT NULL), i.e. it was edited at least once

Revision is detected with EXISTS (stops at the first non-initial version) rather
than COUNT(*) > 1, which is markedly faster over the large PostVersion table.

Dependency:
    pip install mysql-connector-python

Example:
    python extract_answer_list.py                       # python, default output
    python extract_answer_list.py --tag java --output files/acceptedWithVersionAnswer.txt
    python extract_answer_list.py --require-code-block   # only answers containing code
"""

import argparse
import sys
from pathlib import Path

try:
    import mysql.connector
except ImportError:
    sys.exit("Missing dependency: pip install mysql-connector-python")

# Repo layout: this script lives in <repo>/analysis/, the Java stage reads from <repo>/files/
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "files" / "acceptedWithVersionAnswer_python.txt"

FETCH_BATCH = 10_000


def resolve_tag_id(cursor, tag_name):
    """Return the Tags.Id for a tag name, or exit if it is not found."""
    cursor.execute("SELECT Id, Count FROM Tags WHERE TagName = %s", (tag_name,))
    row = cursor.fetchone()
    if row is None:
        sys.exit(f"Tag '{tag_name}' not found in the Tags table.")
    tag_id, tag_count = row
    print(f"Tag '{tag_name}' -> TagId {tag_id} ({tag_count:,} questions)")
    return tag_id


def build_query(tag_id, require_code_block):
    """Assemble the answer-selection SQL for the given tag id."""
    code_block_clause = ""
    if require_code_block:
        code_block_clause = (
            "\n  AND EXISTS (SELECT 1 FROM PostBlockVersion c "
            "WHERE c.PostId = a.Id AND c.PostBlockTypeId = 2)"
        )
    return f"""
        SELECT a.Id
        FROM Posts q
        JOIN PostTags pt ON pt.PostId = q.Id AND pt.TagId = {tag_id}
        JOIN Posts    a  ON a.Id = q.AcceptedAnswerId
        WHERE q.PostTypeId = 1
          AND EXISTS (SELECT 1 FROM PostVersion pv
                      WHERE pv.PostId = a.Id AND pv.PredPostHistoryId IS NOT NULL){code_block_clause}
        ORDER BY a.Id
    """


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--user", default="root")
    parser.add_argument("--password", default="")
    parser.add_argument("--database", default="sotorrent")
    parser.add_argument("--tag", default="python", help="Question tag to filter on (default: python)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Output file (one answer Id per line)")
    parser.add_argument("--require-code-block", action="store_true",
                        help="Only include answers that contain at least one code block")
    args = parser.parse_args()

    db = mysql.connector.connect(host=args.host, user=args.user,
                                 password=args.password, database=args.database)
    try:
        cursor = db.cursor()
        tag_id = resolve_tag_id(cursor, args.tag)

        query = build_query(tag_id, args.require_code_block)
        print("Running answer-selection query (this may take several minutes)...")
        cursor.execute(query)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with open(args.output, "w", encoding="utf-8") as out:
            while True:
                rows = cursor.fetchmany(FETCH_BATCH)
                if not rows:
                    break
                out.write("".join(f"{row[0]}\n" for row in rows))
                count += len(rows)
                print(f"  ...{count:,} answer ids written", end="\r", flush=True)

        cursor.close()
        print(f"\nDone. Wrote {count:,} answer ids to: {args.output}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
