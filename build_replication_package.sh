#!/usr/bin/env bash
#
# Assemble the Zenodo replication package for the Python/JavaScript replication study.
#
# Copies the subset of this repository that a reader needs to reproduce the technical
# report, preserving the relative layout the scripts assume (analysis/, files/,
# technical-report/), then regenerates the two derived result files and writes a
# checksum manifest.
#
#   ./build_replication_package.sh            build into replication-package/
#   ./build_replication_package.sh --zip      also produce replication-package.zip
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$REPO_ROOT/replication-package"
PY="$REPO_ROOT/.venv/bin/python3"

MAKE_ZIP=0
[[ "${1:-}" == "--zip" ]] && MAKE_ZIP=1

echo "==> clearing $OUT"
rm -rf "$OUT"
mkdir -p "$OUT"/{analysis/so-gh_clones,files,technical-report/figures,results}

echo "==> analysis scripts and notebooks"
cp "$REPO_ROOT"/analysis/extract_answer_list.py \
   "$REPO_ROOT"/analysis/python_rq1_stats.py \
   "$REPO_ROOT"/analysis/levenshtein_stats.py \
   "$REPO_ROOT"/analysis/aggregate_so_gh_clones.py \
   "$OUT/analysis/"
cp "$REPO_ROOT"/analysis/python_revision_extraction.ipynb \
   "$REPO_ROOT"/analysis/javascript_revision_extraction.ipynb \
   "$REPO_ROOT"/analysis/python_rq1_stats.ipynb \
   "$REPO_ROOT"/analysis/javascript_rq1_stats.ipynb \
   "$OUT/analysis/"

echo "==> RQ1 data (edit distances, ~225 MB)"
cp "$REPO_ROOT"/analysis/levenshtein_distances_python.csv \
   "$REPO_ROOT"/analysis/levenshtein_distances_javascript.csv \
   "$OUT/analysis/"

echo "==> RQ1 histograms produced by the notebooks"
cp "$REPO_ROOT"/analysis/post_revisions_histogram.pdf \
   "$OUT/analysis/python_post_revisions_histogram.pdf"
cp "$REPO_ROOT"/analysis/javascript_post_revisions_histogram.pdf \
   "$OUT/analysis/"

echo "==> RQ2 clone-search results"
cp -R "$REPO_ROOT"/analysis/so-gh_clones/. "$OUT/analysis/so-gh_clones/"

echo "==> answer id lists"
cp "$REPO_ROOT"/files/acceptedWithVersionAnswer_python.txt \
   "$REPO_ROOT"/files/acceptedWithVersionAnswer_javascript.txt \
   "$OUT/files/"

echo "==> report sources"
cp "$REPO_ROOT"/technical-report/report.tex \
   "$REPO_ROOT"/technical-report/references.bib \
   "$REPO_ROOT"/technical-report/Makefile \
   "$REPO_ROOT"/technical-report/make_figures.py \
   "$OUT/technical-report/"
cp "$REPO_ROOT"/technical-report/figures/*.pdf \
   "$REPO_ROOT"/technical-report/figures/*.png \
   "$OUT/technical-report/figures/"
cp "$REPO_ROOT"/technical-report/notes-paper.md \
   "$REPO_ROOT"/technical-report/notes-results-python.md \
   "$REPO_ROOT"/technical-report/notes-results-javascript.md \
   "$REPO_ROOT"/technical-report/notes-rq2-clones.md \
   "$OUT/technical-report/"

echo "==> built report"
cp "$REPO_ROOT"/technical-report/report.pdf "$OUT/replication_study.pdf"

echo "==> regenerating derived results"
"$PY" "$OUT/analysis/levenshtein_stats.py" --json "$OUT/results/levenshtein_stats.json" \
    > "$OUT/results/levenshtein_stats.txt"
"$PY" "$OUT/analysis/aggregate_so_gh_clones.py" --json "$OUT/results/rq2_summary.json" \
    > "$OUT/results/rq2_summary.txt"
cp "$OUT/results/rq2_summary.json" "$OUT/technical-report/rq2_summary.json"

echo "==> docs"
cp "$REPO_ROOT"/replication-package-files/README.md "$OUT/README.md"
cp "$REPO_ROOT"/replication-package-files/CITATION.cff "$OUT/CITATION.cff"
cp "$REPO_ROOT"/replication-package-files/requirements.txt "$OUT/requirements.txt"
cp "$REPO_ROOT"/LICENSE "$OUT/LICENSE"

echo "==> stripping macOS cruft"
find "$OUT" \( -name '.DS_Store' -o -name '._*' \) -delete
find "$OUT" -name '__pycache__' -type d -exec rm -rf {} +

echo "==> checksum manifest"
( cd "$OUT" && find . -type f ! -name MANIFEST.sha256 -print0 \
    | sort -z | xargs -0 shasum -a 256 > MANIFEST.sha256 )

echo "==> done: $(du -sh "$OUT" | cut -f1), $(find "$OUT" -type f | wc -l | tr -d ' ') files"

if [[ $MAKE_ZIP -eq 1 ]]; then
    echo "==> zipping"
    rm -f "$REPO_ROOT/replication-package.zip"
    ( cd "$REPO_ROOT" && zip -qr replication-package.zip replication-package -x '*.DS_Store' )
    echo "==> $(du -sh "$REPO_ROOT/replication-package.zip" | cut -f1) replication-package.zip"
fi
