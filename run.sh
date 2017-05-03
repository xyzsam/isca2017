#!/bin/bash
#
# This is a set of commonly run commands. I've grouped them into categories.
# You'll probably need to change filenames anyways though.

# Conflict identification
# -----------------------
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv mark-collaborators > results/step1_pcconflicts
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv find-conflicts

# PC/paper partitioning
# ---------------
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv partition-pc
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv partition-papers --existing-update-csv "update_combined.csv"
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv partition-papers --use-existing-paper-partitions --existing-update-csv "update_combined.csv"
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv partition-papers \
#   --use-existing-paper-partitions --existing-update-csv "update_combined.csv"

# Misc
# ----
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo-tags.csv data/institutions.csv analyze-topics
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv export-preferences
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv merge-conflicts-assignments
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv pc-chair-coi --existing-update-csv "update_combined.csv"
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv pc-meeting-plots --existing-update-csv "correct/update_all_conflicts_including_orig.csv" --review-file data/isca2017db-reviews.txt --load
# python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv upload-reviews --existing-update-csv "correct/update_all_conflicts_including_orig.csv" --review-file data/isca2017db-reviews.txt --load
