# Partition papers into Friday/Saturday groups.
#
# Partitioning is done to minimize the number of overall conflicts, based on PC
# partitioning results.
#
# Note: this should be done after all the new conflicts we found are updated.

import random
import unicodecsv as csv

def flip(prob):
  return random.random() < prob

def compute_combined_score(papers, pc):
  """ Compute the total number of conflicts for each day. """
  total_conflicts = 0
  for paper in papers:
    for c in paper.pc_conflicts:
      if c in pc:
        total_conflicts += 1
  return total_conflicts

def partition_papers_once(friday_pc, saturday_pc, paperdb):
  """ Create one partitioning of papers. """
  friday_papers = []
  saturday_papers = []
  num_papers = len(paperdb.orig)
  for paper in paperdb:
    # If a paper's authors contains a PC member, add the paper to the opposite
    # day.
    is_pc_paper = False
    for author in paper.authors:
      if author.is_pc and not author.is_epc:
        is_pc_paper = True
        if author in friday_pc:
          saturday_papers.append(paper)
        else:
          friday_papers.append(paper)
        break

    # Otherwise, add it to any day with 1/2 probability.
    if not is_pc_paper:
      if flip(0.5):
        friday_papers.append(paper)
      else:
        saturday_papers.append(paper)


  return friday_papers, saturday_papers

def partition_papers(friday_pc, saturday_pc, paperdb):
  """ Randomly partition papers into Friday/Saturday groups. """
  X = 100  # num trials.

  min_score = 10000
  best_partition = ()
  for i in range(X):
    friday_papers, saturday_papers = partition_papers_once(
        friday_pc, saturday_pc, paperdb)
    friday_score = compute_combined_score(friday_papers, friday_pc)
    saturday_score = compute_combined_score(saturday_papers, saturday_pc)
    total_score = friday_score + saturday_score
    if total_score < min_score:
      min_score = total_score
      best_partition = (friday_papers, saturday_papers)
      print min_score

  return best_partition

def import_paper_partition(fname, paperdb):
  """ Import a previously generated paper partition. """
  group = []
  with open(fname, "r") as f:
    for line in f:
      split = line.split()
      # First element looks like '16:'.
      pid = int(split[0][:-1])
      paper = paperdb[pid]
      group.append(paper)
  return group

def export_paper_partition(papergroup, label):
  """ Export the list of papers in this group. """
  with open("%s_papers.txt" % label, "wb") as f:
    for paper in papergroup:
      f.write("%d: " % paper.id + paper.title.encode("utf-8") + "\n")

def export_paper_spreadsheet(papergroup, pcgroup, label):
  """ Export a spreadsheet of papers and PC members per group. """
  with open("%s_papers.csv" % label, "wb") as f:
    header = [str(paper.id) for paper in papergroup]
    f.write(",")
    f.write(",".join(header))
    f.write("\n")
    for member in pcgroup:
      line = member.name + ","
      for paper in papergroup:
        if member in paper.pc_conflicts:
          line += "C,"
        else:
          line += ","
      f.write(line.encode("utf-8") + "\n")

def merge_paper_spreadsheets(old_sheet_fname, new_sheet_fname, label):
  """ Take two paper spreadsheets and merge them into one.

  They should have the same dimensions. Cells with multiple data will be
  labeled as such.
  """
  old_sheet = []
  new_sheet = []
  old_sheet_header = []
  new_sheet_header = []
  with open(old_sheet_fname, "r") as f:
    reader = csv.reader(f, delimiter=",")
    old_sheet_header = next(reader, None)
    for row in reader:
      old_sheet.append(row)

  with open(new_sheet_fname, "r") as f:
    reader = csv.reader(f, delimiter=",")
    new_sheet_header = next(reader, None)
    for row in reader:
      new_sheet.append(row)

  # List of papers must be the same.
  assert(old_sheet_header == new_sheet_header)
  assert(len(old_sheet) == len(new_sheet))
  num_columns = len(old_sheet_header)
  num_rows = len(old_sheet)

  merged_sheet = []
  for row in range(num_rows):
    merged_row = []
    # Verify first column names.
    assert(old_sheet[row][0] == new_sheet[row][0])
    merged_row.append(old_sheet[row][0])
    for col in range(1, num_columns):
      old_val = old_sheet[row][col]
      new_val = new_sheet[row][col]
      if old_val.upper() == "C" or old_val.upper() == "":
        # If old value was a conflict or empty, ignore it and use the new
        # value.
        merged_row.append(new_val)
      else:
        # We had something else here, like a preference score.
        if new_val.upper() == "C":
          # If the new value was a conflict, then mark this as problematic.
          merged_row.append("X (%s)" % old_val)
        else:
          # Otherwise, use the old value.
          merged_row.append(old_val)

    merged_sheet.append(merged_row)

  # Merging is done. Write the output.
  with open("%s_merged_papers.csv" % label, "wb") as f:
    writer = csv.writer(f, delimiter=",")
    writer.writerow(old_sheet_header)
    for row in merged_sheet:
      writer.writerow(row)

def merge_assignments_with_spreadsheet(
    assignments_fname, spreadsheet_fname, outfname, pcdb):
  """ Merge a conflicts+preferences spreadsheet with assignments.

  The assigned reviewers+PCs will have SELECTED (X) in their cells,
  where X was the original value of the cell.
  """
  assignments = []
  spreadsheet = []
  with open(assignments_fname, "r") as f:
    reader = csv.reader(f, delimiter=",")
    for row in reader:
      assignments.append(row)

  papers = []
  with open(spreadsheet_fname, "r") as f:
    reader = csv.reader(f, delimiter=",")
    papers = reader.next()
    for row in reader:
      spreadsheet.append(row)
  num_columns = len(papers)

  for row in assignments[1:]:
    paperid = int(row[0])
    email = row[2]
    pcmember = pcdb[pcdb.getid(email, field="email")]
    pcmember.assignments.append(paperid)

  merged_sheet = []
  distribution = dict((i, 0) for i in range(1, 11))
  distribution["None"] = 0

  per_pc_member = {}
  for row in range(len(spreadsheet)):
    merged_row = []
    pcname = spreadsheet[row][0]
    if pcname == "":
      continue
    pcmember = pcdb[pcdb.getid(pcname)]
    merged_row.append(pcname)
    for col in range(3, num_columns):
      paperid = int(papers[col])
      old_val = spreadsheet[row][col]
      if old_val.upper() == "C":
        # If old value was a conflict, keep it.
        merged_row.append(old_val)
      else:
        # If there was either nothing here, or a score preference, AND this
        # pcmember was selected to review this paper, then mark it as such.
        if paperid in pcmember.assignments:
          new_val = "SELECTED (%s)" % old_val

          pcpref = spreadsheet[row][col]
          try:
            pcpref = int(pcpref)
            distribution[pcpref] += 1
          except ValueError as e:
            distribution["None"] += 1

          if pcmember.name in per_pc_member:
            per_pc_member[pcmember.name] += 1
          else:
            per_pc_member[pcmember.name] = 1

        else:
          new_val = old_val
        merged_row.append(new_val)

    merged_sheet.append(merged_row)

  with open(outfname, "w") as f:
    writer = csv.writer(f, delimiter=",")
    writer.writerow(papers[2:])
    for row in merged_sheet:
      writer.writerow(row)

  print "Assignments by preference score."
  for key, val in distribution.iteritems():
    print key, ",", val

  print "Assignments by PC member:"
  for key, val in per_pc_member.iteritems():
    print key, ",", val

def print_paper_summaries(papergroup, outfname, pcdb):
  pcchair = pcdb[pcdb.getid("DAVID BROOKS")]
  with open(outfname, "w") as f:
    output = []
    for paper in papergroup:
      # In case we only want to print Chair conflicts.
      # if not pcchair in paper.pc_conflicts:
      #   continue
      output.append(str(paper.id) + ":" + paper.title.encode("utf-8"))
      for author in paper.authors:
        output.append(" " + author.name.encode("utf-8"))
      output.append("Abstract:")
      output.append(paper.abstract.encode("utf-8"))
      output.append("================")

    for row in output:
      f.write(row + "\n")
