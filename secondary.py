# Secondary functions.
#
# Mostly used for manipulation of spreadsheets and other csvs.

import codecs
import sys
import export2hotcrp
import partitionpapers
import partitionpc
import plots

def count_topics():
  topics_by_paper = {}
  topics_by_pc = {}
  for paper in paperdb:
    for topic in paper.topics:
      if not topic in topics_by_paper:
        topics_by_paper[topic] = 1
      else:
        topics_by_paper[topic] += 1

def try_pre_process(args, paperdb, pcdb, instdb):
  if args.mode == "analyze-topics":
    count_topics()
    sys.exit()

  if args.mode == "upload-reviews":
    with codecs.open("isca2017db-reviews-form-filled.txt", encoding="utf-8", mode="w") as f:
      header = ("==+== ISCA 2017 Paper Review Forms\n"
               "==-== DO NOT CHANGE LINES THAT START WITH \"==+==\" UNLESS DIRECTED!\n"
               "==-== For further guidance, or to upload this file when you are done, go to:\n"
               "==-== https://isca2017.eecs.harvard.edu/offline\n")
      print >>f, header
      for paper in paperdb:
        for review in paper.reviews:
          review.print_offline_form(f)
    sys.exit()

  if args.mode == "export-preferences":
    export2hotcrp.export_review_preferences(
        "saturday_scored_papers.csv",
        "saturday-preferences-update.csv",
        pcdb)
    sys.exit()

  if args.mode == "export-pc-partition-tags":
    friday_pc = partitionpc.read_partition_file(
        "pcpartitions/friday_group.txt", pcdb)
    saturday_pc = partitionpc.read_partition_file(
        "pcpartitions/saturday_group.txt", pcdb)
    export2hotcrp.export_pc_partition_tags(
        "pc-tags-update.csv", friday_pc, saturday_pc)
    sys.exit()

  if args.mode == "merge-conflicts-assignments":
    partitionpapers.merge_assignments_with_spreadsheet(
        "isca2017db-saturday-assignments-no-db-conflicts.csv",
        "saturday_scored_papers.csv",
        "david-saturday-paper-assignments-merged.csv",
        pcdb)
    # partitionpapers.merge_paper_spreadsheets(
    #     "data/friday-papers-assigned.csv", "friday_papers.csv", "friday")
    sys.exit()

  if args.mode == "export-pc-chair-conflicts-spreadsheet":
    friday_pc = partitionpc.read_partition_file(
        "pcpartitions/friday_group.txt", pcdb)
    saturday_pc = partitionpc.read_partition_file(
        "pcpartitions/saturday_group.txt", pcdb)
    friday_papers = partitionpapers.import_paper_partition(
        "paperpartitions/friday_papers.txt", paperdb)
    saturday_papers = partitionpapers.import_paper_partition(
        "paperpartitions/saturday_papers.txt", paperdb)
    partitionpapers.export_pc_chair_conflicts_spreadsheet(
        friday_pc, friday_papers, "friday_pc_chair_conflicts.csv")
    # partitionpapers.export_paper_spreadsheet(
    #     saturday_papers, saturday_pc, "_saturday")
    sys.exit()

def try_post_process(args, paperdb, pcdb, instdb):
  if args.mode == "pc-chair-coi":
    # Prepare data for person to take over David's conflicts.
    friday_papers = partitionpapers.import_paper_partition(
        "paperpartitions/saturday_papers.txt", paperdb)
    partitionpapers.print_paper_summaries(friday_papers, "saturday_paper_summaries.txt", pcdb)
    sys.exit()

    friday_pc = partitionpc.read_partition_file(
        "pcpartitions/saturday_group.txt", pcdb)
    partitionpc.print_topics_by_pc_members(pcdb, "pc_topics.txt")
    partitionpc.print_topic_pc_member_spreadsheet(pcdb, "pc_topics.csv")
    sys.exit()

  if args.mode == "pc-meeting-plots":
    plots.plot_pc_meeting(paperdb, pcdb, instdb)
