# Reads the list of PC members.

import unicodecsv as csv
import codecs
import re

import base

class Person(base.BaseObj):
  _id = 0

  def __init__(self, persondict):
    super(Person, self).__init__()
    first         = base.dict_default(persondict, "first", "")
    last          = base.dict_default(persondict, "last", "")
    email         = base.dict_default(persondict, "email", "")
    affiliations  = base.dict_default(persondict, "affiliation", "")
    conflicts     = base.dict_default(persondict, "collaborators", "")
    tags          = base.dict_default(persondict, "tags", "")
    self.name = u"{0} {1}".format(first, last)
    self.name = self.name.upper()
    self.email = email
    self.affiliations = unicode(affiliations).encode("utf-8")
    self.conflicts = unicode(conflicts).encode("utf-8")
    self.id = Person._id
    self.is_pc = "pc" in tags
    self.is_epc = "epc" in tags
    self.tags = tags.split()
    Person._id += 1

    # List of papers that they were assigned.
    self.assignments = []

    # Parse topics list.
    # Preferences go [-2, -1, <empty>, 2, 4]
    self.topics = []
    for field, pref in persondict.iteritems():
      if field.startswith("topic:"):
        if len(pref) == 0:
          continue
        pref = int(pref)
        if pref >= 2:
          self.topics.append(field[7:])

  def process_affiliations(self, instdb):
    """ Convert names of affiliations into Institution objects. """
    if isinstance(self.affiliations, list):
      # If this has already been done, then don't try to do it again.
      return
    affiliations = []
    inst_names = re.split(";| AND |/", self.affiliations.decode("utf-8").upper())
    for inst in inst_names:
      inst = re.sub("UNIVERSITY|COLLEGE", "", inst.upper().strip())
      instid = instdb.find_exact_or_closest(inst)
      if instid != -1:
        affiliations.append(instdb[instid])

    self.affiliations = list(affiliations)

  def process_conflicts(self, instdb):
    """ Split conflicts into a set.

    Don't call this until after calling process_affiliations().
    """
    if isinstance(self.conflicts, list):
      return
    result = re.sub("\(.+\)|;.+|,.+|:.+|UNIVERSITY|COLLEGE", "", self.conflicts.upper())
    conflicts = result.split("\n")
    unique_conflicts = set()
    self.conflicts = []
    for c in conflicts:
      c = unicode(c, encoding="utf-8")
      instid = instdb.find_exact_or_closest(c)
      if instid != -1:
        self.affiliations.append(instdb[instid])
      else:
        self.conflicts.append(c)

  def __unicode__(self):
    affiliations_str = ""
    if isinstance(self.affiliations, str):
      affiliations_str = self.affiliations;
    elif isinstance(self.affiliations, list):
      affiliations_str = u",".join([inst.name for inst in self.affiliations])
    return u"{0} ({1})".format(self.name, affiliations_str)

  def __str__(self):
    return unicode(self).encode("utf-8")

  def __repr__(self):
    return str(self)

  def __eq__(self, other):
    if isinstance(other, Person):
      return other.id == self.id
    return False

class ProgramCommitteeDB(base.BaseDB):
  def __init__(self, pc_list):
    super(ProgramCommitteeDB, self).__init__(pc_list)

  def find_members_with_affiliation(self, instid):
    result = []
    for member in self:
      if instid in member.affiliations:
        result.append(member)
    return result

def read_pcdb(fname):
  pc = []
  first = True
  with open(fname, "rb") as f:
    reader = csv.reader(f, delimiter=",")
    header = next(reader, None)
    for row in reader:
      person_dict = dict(zip(header, row))
      pc.append(Person(person_dict))

  return ProgramCommitteeDB(pc)
