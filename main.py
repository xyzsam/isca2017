#!/bin/env python
#
# Finds all PC conflicts for each paper.

import argparse
import cPickle as pickle
import sys
import re
from fuzzywuzzy import fuzz

import export2hotcrp
import institutions
import partitionpapers
import partitionpc
import programcommittee
import secondary
import submissions
import plots
import reviews

paperdb = None
pcdb = None
instdb = None
reviewdb = None

def mark_collaborators_on_pc_conflicts():
  """ Step 1: Fix PC members that appear as collaborators.

  For each PC member, query the paper database to find a list
  of papers that may contain that member in the collaborators field.
  Print out PC member name, the name of the matching field.
  """
  for pc_member in pcdb:
    print "================================="
    print "PC member ", pc_member.id, "##", unicode(pc_member.name).encode("utf-8")
    print "================================="
    for p in paperdb:
      collab_name, score = p.find_collaborator(pc_member.name)
      collab_name = unicode(collab_name).encode("utf-8")
      if score >= 80:
        print p.id, "##", score, ":", collab_name
      elif score > 70:
        print p.id, "##", score, ":", collab_name, "!!! VERIFY !!!"

def read_step1_manual_file(fname):
  """ Reads a file that has fixed all the errors from step 1. """
  name_re = re.compile("(?<=## ).*")
  with open(fname, "rb") as f:
    curr_pc_name = ""
    for line in f:
      line = unicode(line, encoding="utf-8")
      if line.startswith("==="):
        continue
      split = line.split()
      if line.startswith("PC member"):
        curr_pc_name = re.findall(name_re, line)[0]
        continue
      paper_id = int(split[0])
      paper = paperdb[paper_id]
      assert(curr_pc_name != "")
      pc_id = pcdb.getid(curr_pc_name)
      assert(pc_id != -1)
      paper.pc_conflicts.add(pcdb[pc_id])
  for paper in paperdb:
    print paper
    print paper.pc_conflicts

def mark_pcs_in_author_institutions_conflicts():
  """ Step 2: Find PC members who share institutions with authors. """
  for paper in paperdb:
    print paper
    conflicts = set()
    for author in paper.authors:
      for affiliation in author.affiliations:
        # Get the primary name for this affiliation. If we couldn't find it,
        # then there can be no conflict, skip this and move on.
        print affiliation
        instid = instdb.getid(affiliation.name)
        if instid == -1:
          continue
        print instdb[instid]
        # Now find all PC members with this institution.
        matching_pc_members = pcdb.find_members_with_affiliation(instid)
        for m in matching_pc_members:
          conflicts.add(m)
    paper.pc_conflicts |= conflicts
    print paper.pc_conflicts

def mark_institutions_in_other_conflicts():
  """ Step 3: Identify institution names in "Other Conflicts. """
  for paper in paperdb:
    print paper
    ids = set()
    names = []  # For visualization.
    for collab in paper.collaborators:
      if collab == "NONE":
        continue
      instid = instdb.find_exact_or_closest(collab, scorer=fuzz.ratio)
      if instid != -1:
        ids.add(instid)
        names.append(instdb[instid])

    # print names
    # Now find all PC members with this institution.
    conflicts = set()
    for instid in ids:
      matching_pc_members = pcdb.find_members_with_affiliation(instid)
      for m in matching_pc_members:
        conflicts.add(m)
    paper.pc_conflicts |= conflicts
    print paper.pc_conflicts

def import_update_csv(fname):
  """ Import an existing update CSV file. """
  with open(fname, "r") as f:
    f.next()  # Skip the header.
    for line in f:
      line = line.strip()
      fields = line.split(",")
      pid = int(fields[0])
      assignment = fields[1]
      email = fields[2]
      pcid = pcdb.getid(email, field="email")
      assert(pcid != -1)
      paperdb[pid].pc_conflicts.add(pcdb[pcid])

def export_update_csv(suff=""):
  update_csv = open("update%s.csv" % suff, "w")
  update_csv.write("paper,assignment,email\n")
  for paper in paperdb:
    conflicts = sorted(paper.pc_conflicts)
    for conflict in conflicts:
      row = "{0},{1},{2}\n".format(paper.id, "conflict", conflict.email)
      update_csv.write(row)

  update_csv.close()

def clear_pc_conflicts():
  for paper in paperdb:
    paper.pc_conflicts = set()

def subtract_orig_pc_conflicts():
  for paper in paperdb:
    paper.pc_conflicts -= paper.orig_pc_conflicts

def load_from_pickle_file():
  with open("data.pickle", "rb") as f:
    obj = pickle.load(f)
    global paperdb
    global pcdb
    global instdb
    global reviewdb
    paperdb = obj["paperdb"]
    pcdb = obj["pcdb"]
    instdb = obj["instdb"]
    reviewdb = obj["reviewdb"]

def store_to_pickle_file(paperdb, pcdb, instdb, reviewdb):
  obj = {"paperdb": paperdb,
         "pcdb": pcdb,
         "instdb": instdb,
         "reviewdb": reviewdb}

  with open("data.pickle", "wb") as f:
    pickle.dump(obj, f)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("paperdb", help="JSON dump of all submissions.")
  parser.add_argument("pcdb", help="CSV dump of all PC+ERC members.")
  parser.add_argument("instdb",
      help="CSV file of all institutions and possible spellings.")
  parser.add_argument("mode",
      choices=["analyze-topics", "find-conflicts", "mark-collaborators",
               "partition-pc", "partition-papers", "export-preferences",
               "export-pc-partition-tags", "merge-conflicts-assignments",
               "pc-chair-coi", "pc-meeting-plots", "upload-reviews"])
  parser.add_argument("--load", action="store_true",
      help="Load a pickle file.")
  parser.add_argument("--review-file", help="Dump of all reviews.")
  parser.add_argument("--separate-steps", action="store_true",
      help="Separate conflict update csvs into each step.")
  parser.add_argument("--use-existing-paper-partitions", action="store_true",
      help="Import existing paper partitions from this file, rather than "
      "regenerating them randomly.")
  parser.add_argument("--existing-update-csv",
      help="Import already generating conflict updates from this csv.")

  args = parser.parse_args()
  global paperdb
  global pcdb
  global instdb
  global reviewdb
  if args.load:
    load_from_pickle_file()
  else:
    paperdb = submissions.read_paperdb(args.paperdb)
    pcdb = programcommittee.read_pcdb(args.pcdb)
    instdb = institutions.read_instdb(args.instdb)
    if args.review_file:
      reviewdb = reviews.read_reviewdb(args.review_file)
      reviews.merge_with_paperdb(reviewdb, paperdb)

    ########################################
    ##### Processing (takes some time) #####
    ########################################

    for member in pcdb:
      member.process_affiliations(instdb)
      member.process_conflicts(instdb)

    for p in paperdb:
      p.process_pc_conflicts(pcdb)
      p.process_authors(pcdb)
      for author in p.authors:
        author.process_affiliations(instdb)

    store_to_pickle_file(paperdb, pcdb, instdb, reviewdb)

    ##################################
    ##################################

  secondary.try_pre_process(args, paperdb, pcdb, instdb)

  if args.mode == "partition-pc":
    friday, saturday = partitionpc.partition_pc(pcdb, "smart")
    partitionpc.print_partition(friday, "friday", pcdb)
    partitionpc.print_partition(saturday, "saturday", pcdb)
    partitionpc.print_partition_diff(friday, saturday, pcdb)
    partitionpc.verify_partition(friday, partitionpc.FRIDAY_TAG)
    partitionpc.verify_partition(saturday, partitionpc.SATURDAY_TAG)
    partitionpc.verify_all_pc_members_present(friday, saturday, pcdb)
    sys.exit()

  if args.existing_update_csv:
    import_update_csv(args.existing_update_csv)

  secondary.try_post_process(args, paperdb, pcdb, instdb)

  # Run this function first, generate the stdout file, and fix everything, then
  # load that into read_step1_manual_file().
  if args.mode == "mark-collaborators":
    mark_collaborators_on_pc_conflicts()
    return

  if args.mode == "find-conflicts" or args.mode == "partition-papers":
    if args.existing_update_csv:
      import_update_csv(args.existing_update_csv)
    else:
      if args.separate_steps:
        clear_pc_conflicts()
        read_step1_manual_file("results/step1_pcconflicts")
        subtract_orig_pc_conflicts()
        export_update_csv("_step1")

        clear_pc_conflicts()
        mark_pcs_in_author_institutions_conflicts()
        subtract_orig_pc_conflicts()
        export_update_csv("_step2")

        clear_pc_conflicts()
        mark_institutions_in_other_conflicts()
        subtract_orig_pc_conflicts()
        export_update_csv("_step3")
        print "With separate steps, we cannot do anything more."
        sys.exit()

      else:
        clear_pc_conflicts()
        read_step1_manual_file("results/step1_pcconflicts")
        mark_pcs_in_author_institutions_conflicts()
        mark_institutions_in_other_conflicts()

        subtract_orig_pc_conflicts()
        export_update_csv("_combined")

  if args.mode == "partition-papers":
    friday_pc = partitionpc.read_partition_file(
        "pcpartitions/friday_group.txt", pcdb)
    saturday_pc = partitionpc.read_partition_file(
        "pcpartitions/saturday_group.txt", pcdb)
    score = partitionpc.compute_combined_score(friday_pc, saturday_pc, {})
    print "PC score: ", score
    partitionpc.print_partition_diff(friday_pc, saturday_pc, pcdb)
    partitionpc.print_partition(friday_pc, "friday", pcdb)
    partitionpc.print_partition(saturday_pc, "saturday", pcdb)

    if args.use_existing_paper_partitions:
      friday_papers = partitionpapers.import_paper_partition(
          "paperpartitions/friday_papers.txt", paperdb)
      saturday_papers = partitionpapers.import_paper_partition(
          "paperpartitions/saturday_papers.txt", paperdb)
      friday_score = partitionpapers.compute_combined_score(
          friday_papers, friday_pc)
      saturday_score = partitionpapers.compute_combined_score(
          saturday_papers, saturday_pc)
      partitionpapers.export_paper_spreadsheet(
          friday_papers, pcdb, "friday")
      partitionpapers.export_paper_spreadsheet(
          saturday_papers, pcdb, "saturday")
      print "Friday score:", friday_score
      print "Saturday score:", saturday_score
    else:
      friday_papers, saturday_papers = partitionpapers.partition_papers(
          friday_pc, saturday_pc, paperdb)
      partitionpapers.export_paper_partition(friday_papers, "friday")
      partitionpapers.export_paper_partition(saturday_papers, "saturday")
      partitionpapers.export_paper_spreadsheet(
          friday_papers, friday_pc, "friday")
      partitionpapers.export_paper_spreadsheet(
          saturday_papers, saturday_pc, "saturday")

if __name__ == "__main__":
  main()
