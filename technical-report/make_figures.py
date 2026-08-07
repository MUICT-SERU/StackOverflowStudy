#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate the figures for the Python and JavaScript replication technical report.

Produces, in technical-report/figures/:

  levenshtein_boxplots.png              Python and JavaScript edit sizes, outliers shown
  levenshtein_boxplots_no_outliers.png  the same, fliers hidden so the boxes are legible
  rq2_edits_by_group.pdf                matched answer edits by project popularity group

The boxplots are raster images because the outlier variant plots over a million flier
markers; as vector PDFs they are large and slow to render. The other figures stay vector.

The revision-count histograms are copied from the analysis directory rather than
regenerated, because the per-answer revision counts live only in SOTorrent.

Run with the project virtualenv, which has matplotlib:
    .venv/bin/python3 technical-report/make_figures.py
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPORT_DIR = Path(__file__).resolve().parent
REPO_ROOT = REPORT_DIR.parent
ANALYSIS_DIR = REPO_ROOT / "analysis"
FIG_DIR = REPORT_DIR / "figures"

# Greyscale, so the report prints legibly in black and white.
GREYS = {"python": "#8c8c8c", "javascript": "#4d4d4d"}
GROUP_COLOURS = {"low": "#bfbfbf", "medium": "#8c8c8c", "high": "#4d4d4d"}


def read_distances(path):
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader, None)
        return [int(row[2]) for row in reader if len(row) >= 3]


def boxplots(data, out_path, show_outliers):
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    labels = ["Python", "JavaScript"]
    series = [data["python"], data["javascript"]]
    bp = ax.boxplot(series, vert=False, labels=labels, showfliers=show_outliers,
                    widths=0.55, patch_artist=True,
                    flierprops={"marker": "o", "markersize": 2.5,
                                "markerfacecolor": "none", "alpha": 0.35},
                    medianprops={"color": "black", "linewidth": 1.4})
    for patch, key in zip(bp["boxes"], ("python", "javascript")):
        patch.set_facecolor(GREYS[key])
        patch.set_alpha(0.75)
    ax.set_xlabel("Levenshtein distance (characters)", fontsize=11)
    ax.tick_params(axis="both", labelsize=10)
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    # Written as a raster image rather than a vector one. With outliers shown these
    # plots carry over 1.4 million flier markers between them, which makes a PDF
    # around 1 MB and slow for a viewer to draw.
    fig.savefig(out_path, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(REPORT_DIR)}")


def rq2_bars(summaries, out_path):
    groups = ("low", "medium", "high")
    labels = ["Low-popularity", "Medium-popularity", "High-popularity"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=False)

    for ax, lang, title in zip(axes, ("python", "javascript"),
                               ("Python", "JavaScript")):
        values = [summaries[lang]["groups"][g]["answer_edits"] for g in groups]
        bars = ax.bar(labels, values,
                      color=[GROUP_COLOURS[g] for g in groups],
                      edgecolor="black", linewidth=0.6, width=0.65)
        for bar, value in zip(bars, values):
            ax.annotate(f"{value:,}", (bar.get_x() + bar.get_width() / 2, value),
                        ha="center", va="bottom", fontsize=10)
        ax.set_title(title, fontsize=11)
        ax.set_ylabel("Matched answer edits", fontsize=10)
        ax.set_ylim(0, max(values) * 1.18)
        ax.tick_params(axis="x", labelsize=9, rotation=12)
        ax.tick_params(axis="y", labelsize=9)
        ax.grid(True, axis="y", alpha=0.3)
        ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(out_path, format="pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(REPORT_DIR)}")


def main():
    FIG_DIR.mkdir(exist_ok=True)

    print("reading Levenshtein distances...")
    data = {
        "python": read_distances(ANALYSIS_DIR / "levenshtein_distances_python.csv"),
        "javascript": read_distances(ANALYSIS_DIR / "levenshtein_distances_javascript.csv"),
    }
    for lang, values in data.items():
        print(f"  {lang}: {len(values):,} pairs")

    boxplots(data, FIG_DIR / "levenshtein_boxplots.png", show_outliers=True)
    boxplots(data, FIG_DIR / "levenshtein_boxplots_no_outliers.png", show_outliers=False)

    print("aggregating clone-search results...")
    summary_json = FIG_DIR.parent / "rq2_summary.json"
    subprocess.run(
        [sys.executable, str(ANALYSIS_DIR / "aggregate_so_gh_clones.py"),
         "--json", str(summary_json)],
        check=True, capture_output=True,
    )
    summaries = json.loads(summary_json.read_text())
    rq2_bars(summaries, FIG_DIR / "rq2_edits_by_group.pdf")


if __name__ == "__main__":
    main()
