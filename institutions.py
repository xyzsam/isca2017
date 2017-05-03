# Reads the institution name database.

from bisect import bisect_left
import re

from fuzzywuzzy import fuzz
import base

class Institution(base.BaseObj):
  _id = 0

  def __init__(self, aliases):
    super(Institution, self).__init__()
    self.aliases = []
    for alias in aliases:
      self.aliases.append(alias.strip())
    self.name = self.aliases[0]
    self.id = Institution._id
    Institution._id += 1

  def __eq__(self, other):
    if isinstance(other, Institution):
      return other.id == self.id
    elif isinstance(other, int):
      return other == self.id
    return False

  def __unicode__(self):
    return u"{0}".format(self.name)

  def __str__(self):
    return unicode(self).encode("utf-8")

  def __repr__(self):
    return str(self)

class InstDB(base.BaseDB):
  def __init__(self, inst_list):
    super(InstDB, self).__init__(inst_list)

    # Add all of the aliases for each institution.
    for inst in inst_list:
      for name in inst.aliases:
        self.pairs_.append((name, inst.id))
        self.names_.append(name)
    self.pairs_.sort(key=lambda tup: tup[0])
    self.names_.sort()

  def find_exact_or_closest(self, instname, scorer=fuzz.token_set_ratio):
    """ Find either an exact match or a very close match. """
    if len(instname) == 0:
      return -1

    # Try to find an exact match.
    instid = self.getid(instname)
    if instid != -1:
      return instid

    # Find closest match to this institution.
    match = self.find_closest(instname, scorer=scorer)
    if not match:
      return -1
    score = match["score"]
    if score >= 90:
      return match["id"]
    return -1

def read_instdb(fname):
  institutions = []
  with open(fname, "rb") as f:
    for line in f:
      line = unicode(line, encoding="utf-8")
      split = line.split(",")
      # Remove "University" and "College"
      processed = []
      for s in split:
        s = re.sub("UNIVERSITY|COLLEGE", "", s.upper())
        processed.append(s)
      institutions.append(Institution(processed))

  return InstDB(institutions)
