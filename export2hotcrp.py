# Export functions for HotCRP.

import unicodecsv as csv

def export_review_preferences(fname, outfname, pcdb):
  """ Export review preferences as HotCRP bulk update. """
  total_preferences = 0
  updates = []
  # New header.
  updates.append(["paper", "assignment", "user", "preference"])
  # updates.append(["paper", "assignment", "user", "tag"])
  with open(fname, "r") as f:
    reader = csv.reader(f, delimiter=",")
    header = reader.next()
    # Papers start at column 4.
    header = [int(pid) for pid in header[3:]]
    num_papers = len(header)
    print "Num papers:", num_papers
    for row in reader:
      pcname = row[0]
      if pcname == "DAVID BROOKS" or pcname == "":
        continue
      pcmember = pcdb[pcdb.getid(pcname)]
      for col, paperid in enumerate(header):
        pcpref = row[3+col]

        # if pcpref == "C":
        #   updates.append([paperid, "tag", pcmember.email, "Friday_DB_Conflict"])
        # else:
        #   continue

        try:
          pcpref = int(pcpref)*10
        except (TypeError, ValueError) as e:
          # This was probably either a "C" or a "".
          continue
        total_preferences += pcpref
        updates.append([paperid, "preference", pcmember.email, pcpref])

  with open(outfname, "w") as f:
    writer = csv.writer(f, delimiter=",")
    for row in updates:
      writer.writerow(row)

  print "total pref:", total_preferences

def export_pc_partition_tags(fname, friday_group, saturday_group):
  """ Update PC member tags with their respective Friday/Saturday tags. """
  with open(fname, "w") as f:
    writer = csv.writer(f, delimiter=",")
    updates = []
    updates.append(["email","add_tags","remove_tags"])
    combined_groups = set(friday_group) | set(saturday_group)
    for pc_member in combined_groups:
      if "PC_Either" in pc_member.tags:
        if pc_member in friday_group:
          updates.append([pc_member.email, "PC_Friday,PC_Either_orig", "PC_Either"])
        else:
          updates.append([pc_member.email, "PC_Saturday,PC_Either_orig", "PC_Either"])
      elif "PC_Both" in pc_member.tags:
        if pc_member in friday_group and pc_member in saturday_group:
          updates.append([pc_member.email, "PC_Friday,PC_Saturday,PC_Both_orig", "PC_Both"])
        elif pc_member in friday_group:
          updates.append([pc_member.email, "PC_Friday,PC_Both_orig", "PC_Both"])
        else:
          updates.append([pc_member.email, "PC_Saturday,PC_Both_orig", "PC_Both"])

    for row in updates:
      writer.writerow(row)
