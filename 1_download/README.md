# 1) Downloading files
Natalia Vélez

In this folder:

* `1_1_download_data.py`: Start here! This notebook scrapes data from the public logs. As of the latest update (September 2020), the script tries to do so pretty conservatively—we only take lifelog and maplog files from bigserver2, since that's what we're using in our analyses.
* `1_2_version_history_github.ipynb`: This notebook scrapes the version histories from two repositories: the game files (OneLife) and game data (OneLifeData7). We use the union of the two releases to make the version history.

Notable outputs:

* `outputs/version_history.tsv`: Version history (generated using `1_2`)
