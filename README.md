# StackOverflowStudy (Matcha Study)

This project studies **how Stack Overflow answers get edited over time, and how those
edits relate to the same code appearing in GitHub projects**. It is built around
[SOTorrent](https://empirical-software.engineering/projects/sotorrent/) (a dataset of
SO post version histories) and a curated set of GitHub Java projects.

This `SOPostProcessor/` folder holds the analysis pipeline. The bulk input data and
experiment outputs live one level up in the parent repo:

| Path (relative to this folder) | Contents |
|---|---|
| `../java_files/` | Extracted SO code snippets as `*_original.java` / `*_recent.java` pairs. |
| `../GHProjects/` | Cloned GitHub Java projects. |
| `../Matcha Results/` | Experiment output runs (`matcha_result_*`, `result#*`, config variants). |
| `../GH_selection.csv` / `.xlsx` | Master GitHub project selection with metadata. |

## The pipeline, end to end

### Stage 1 — Java: extract SO edit histories from the SOTorrent MySQL DB

Located in `SOTorrentAnalyzer/`. The data model mirrors SOTorrent's structure:

- **`Post.java`** — one SO answer, holding a linked list of...
- **`PostHistory.java`** — one revision of that answer, holding...
- **`PostBlock.java`** — a text or code block, with links to its *preceding* block in
  the prior revision plus a `precedingSimilarity` score.

**`PostBlockProcessor.java`** is the main driver. It reads answer IDs from
`files/acceptedWithVersionAnswer.txt` (~140k accepted answers that have multiple
versions), queries the `PostBlockVersion` / `PostBlockDiff` tables, builds the object
graph, and serializes it to `posts_data.ser`. It offers four analyses (main enables
options 1 & 2):

- **`calculatePostChanges`** — walks each block's `precedingSimilarity` chain via the
  recursive `checkSimilarity`, classifying each answer as having code changes / text
  changes / both.
- **`calculateSimilarity`** — computes min/max/avg similarity + average days between
  revisions per block, filtering to a similarity band (0.8–0.9) and a minimum edit gap →
  writes `similarity.csv`.
- **`writeDiffFiles`** — emits per-block unified diffs (see naming convention below).

**`PostProcessor.java`** is an older/simpler standalone version of the same import
(writes to `/home/Dreamteam/`).

### Stage 2 — Python: edit-distance analysis

`analysis/code_diff.py` finds `*_original.java` / `*_recent.java` file pairs (extracted
SO code snippets in `../java_files/`), computes the **Levenshtein distance** between the
original and most-recent version of each snippet, and produces stats plus a boxplot
(`levenshtein_boxplot.pdf`). Results are cached in `analysis/levenshtein_distances.csv`
(~233k pairs).

### Stage 3 — Python: GitHub project analysis (the "Matcha" study)

`analysis/analysis.py`:

1. Counts lines of Java code per GitHub project → `code_lines_count.csv`.
2. Joins that to project metadata (`GH_selection_revise_FIXED.csv`) →
   `projects_with_codelines.csv`.
3. Buckets projects into **low / medium / high popularity** groups (using
   `stars_region` / `forks_region` / `watchers_region` all = 1 / 2 / 3).
4. Compares two recommendation types — **`bugfix`** vs **`improvingcode`** — across those
   groups with histograms, boxplots, and statistical tests (Shapiro-Wilk normality +
   Kruskal-Wallis).

`improving_code_vs_gh_groups` breaks down `matcha_subtype` per group from
`improving_code.csv`. The notebook `analysis/read_excel.ipynb` does a lightweight version
of the same group-sum / counts plus a grayscale bar chart of bugfix vs improving-code
counts per GitHub group.

## Key data files

| File | What it is |
|---|---|
| `files/acceptedWithVersionAnswer.txt` | ~140k SO answer IDs (input to Java stage); `_1000` and `2` are smaller test subsets. |
| `similarity.csv` | Per-block similarity + revision-gap stats from Java stage. |
| `analysis/levenshtein_distances.csv` | Original-vs-recent snippet edit distances. |
| `analysis/GH_selection_revise_FIXED.csv` | ~10.6k GitHub projects w/ metadata + bugfix/improvingcode labels. |
| `analysis/projects_with_codelines.csv` | Above joined with LOC counts. |
| `analysis/improving_code.csv` | Subset labeled with `matcha_subtype` categories. |

Also present: `mysql-connector-java-8.0.27.jar` (JDBC driver for the Java stage) and
several Python virtualenvs (`venv`, `env`, `.venv`, `analysis/.venv`) — environments,
not source.

## Running the Java stage (remote GCP server)

**How to access the remote server via SSH browser on GCP**
1. Go to the GCP console, and login with the jarvan-experiment Google account.
2. On the navigation panel on the left side, select `Compute Engine` under the
   `VIRTUAL MACHINES` menu, then select `VM instances`.
3. You will see the `jarvan-exp-1` machine. On the connect column select the drop-down
   arrow and select `Open in browser window`.
4. There you go — you now have access to the remote server.

**How to use the MySQL server on the remote server**
1. On the remote server, use command `mysql -u root -p`.
2. You will be asked for a password. Use the password provided in order to access the
   MySQL server.
3. After that you will be allowed to access the MySQL server as root.
4. There is only one database available, which is `sotorrent`. Use `use sotorrent` to
   select the database.
5. There are two data tables available in the database: `PostBlockVersion` and
   `PostBlockDiff`.
6. You may use SQL commands to query for data such as `select`, `insert`, `delete`, etc.

**How to compile and run the Java program on the remote server**
1. On the remote server, the Java program is located in `/StackOverflowStudy/SOTOrrentAnalyzer/`.
   Run `cd StackOverflowStudy/SOTOrrentAnalyzer/` to change to this directory.
2. There are several Java files, but only one has the main class for running:
   `PostBlockProcessor.java`.
3. Compile with `javac PostBlockProcessor.java`. You may need to change the location of
   the SO answer file in the code.
4. Add the MySQL connector to the Java CLASSPATH:
   `export CLASSPATH=$CLASSPATH:/usr/share/java/mysql-connector-java-8.0.27.jar`.
5. In `PostBlockProcessor.java`, the options for selecting what the program does are near
   the top of `main` (there are 4 options currently). See the file for what each does.
6. Run the Java program with `java PostBlockProcessor`.

**Diff file naming convention**
Diff files follow the pattern
`PostId-PostHistoryId-LocalId-CurrentPostBlockId-PreviousPostBlockId-PostBlockTypeId.txt`,
where `PostBlockTypeId` is either 0 or 1 — 0 is a Text block and 1 is a Code block.

> **Remark:** Sometimes you may hit an error while compiling the Java program where the
> compiler cannot find the `.jar` for SQL. Run
> `export CLASSPATH=$CLASSPATH:/usr/share/java/mysql-connector-java.jar` to bypass it.

## Known issues / cleanup candidates

- **Duplicated group-bucketing logic**: `group_lines_by_categories`,
  `bugfix_recommendations_by_groups`, and `improving_code_recommendations_by_groups` in
  `analysis.py` are near-identical (only the column read differs) — a candidate for
  consolidation.
- **`savePostsToFile` double-prepends `home`**: in `PostBlockProcessor.java`, the call
  site passes `home + "posts_data.ser"` but the method prepends `home` *again*, so the
  write path is doubled up. The read side uses the correct single-`home` path, meaning
  save and load target different paths as written.
