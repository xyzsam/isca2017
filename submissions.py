# Reads a JSON dump of all paper submissions

import json
import re

from fuzzywuzzy import fuzz, process

import programcommittee
import base

class Paper(base.BaseObj):
  def __init__(self, json_obj):
    super(Paper, self).__init__()
    """ Construct class from JSON object. """
    self.status =        base.dict_default(json_obj, "status", "unsubmitted")
    self.collaborators = base.dict_default(json_obj, "collaborators", "")
    self.submitted_at =  base.dict_default(json_obj, "submitted_at", 0)
    self.submission =    base.dict_default(json_obj, "submission", False)
    self.title =         base.dict_default(json_obj, "title", "")
    self.abstract =      base.dict_default(json_obj, "abstract", "")
    self.pid =           base.dict_default(json_obj, "pid", -1)
    self.submitted =     base.dict_default(json_obj, "submitted", False)
    self.authors =       base.dict_default(json_obj, "authors", [])
    self.pc_conflicts =  base.dict_default(json_obj, "pc_conflicts", {})
    self.options =       base.dict_default(json_obj, "options", None)
    self.topics =        base.dict_default(json_obj, "topics", {})
    self.reviews = []

    # For the database abstraction.
    self.id = self.pid
    self.name = self.title

    self.institutional_conflicts = []
    self.process_collaborators()
    self.process_topics()

  def get_average_score(self, post_or_pre_rebuttal="post"):
    total_score = 0
    for review in self.reviews:
      if post_or_pre_rebuttal == "post":
        total_score += review.scores["Post rebuttal overall merit"]
      else:
        total_score += review.scores["Overall merit"]

    return total_score/float(len(self.reviews))

  def contains_author(self, author):
    """ Returns true if the author object is in this paper's author list. """
    return author in self.authors

  def process_pc_conflicts(self, pcdb):
    """ Convert the list of conflicted PC emails into PC author objects. """
    assert(isinstance(self.pc_conflicts, dict))
    pc_emails = [email for email in self.pc_conflicts.iterkeys()]
    pc_members = []
    for email in pc_emails:
      pc_id = pcdb.getid(email, field="email")
      assert(pc_id != -1)
      pc_members.append(pcdb[pc_id])

    self.pc_conflicts = set(pc_members)

    # Keep the original list around so we can find the differences.
    self.orig_pc_conflicts = set(pc_members)

  def process_authors(self, pcdb):
    """ Convert dict into Author class object.

    Since some authors can be PC members, pass the PC DB as well so that we can
    link up Person IDs when possible.
    """
    authors = []
    for author in self.authors:
      # Add the existing PC member object if it exists; otherwise, create a new
      # Person.
      pc_found = False
      if "email" in author:
        pc_id = pcdb.getid(author["email"], field="email")
        if pc_id != -1:
          author = pcdb[pc_id]
          authors.append(author)
          # Add PC conflicts to the current list of collaborators (since we'll
          # deal with them the same way).
          assert(isinstance(author.conflicts, list))
          self.collaborators.extend(author.conflicts)
          pc_found = True
      if not pc_found:
        authors.append(programcommittee.Person(author))
    self.authors = authors

  def process_collaborators(self):
    """ Split the big string into a list. """
    collaborators = self.collaborators.split("\n")
    # Remove the obvious institutions.
    final = []
    for c in collaborators:
      result = re.sub("\(.+\)|;.+|,.+|UNIVERSITY|COLLEGE", "", c.upper())
      result = result.strip()
      if len(result) > 0:
        final.append(result)

    self.collaborators = final

  def process_topics(self):
    self.topics = [topic for topic in self.topics.iterkeys()]

  def mark_institutional_conflicts(self, instdb):
    """ Any collaborators in instdb are actually institutional conflicts. """
    conflicts = []
    nonconflicts = []
    for c in self.collaborators:
      if c in instdb:
        conflicts.append(c)
      else:
        nonconflicts.append(c)
    self.institutional_conflicts = [instdb.getid(c) for c in conflicts]
    self.collaborators = nonconflicts

  def find_collaborator(self, name):
    """ Return the paper's self-reported collaborator that most closely matches @name.

    A tuple containing the name of the matched collaborator and the
    fuzzy-matching score is returned. If a match cannot be found, this returns
    ("", 0).
    """
    if len(name) == 0:
      return ("", 0)
    result = process.extractOne(name.upper(), self.collaborators,
                                scorer=fuzz.ratio)
    if result == None:
      return ("", 0)
    return result

  def __unicode__(self):
    return u"{0}: {1}".format(self.pid, self.name)

  def __str__(self):
    return unicode(self).encode("utf-8")

class PaperDB(base.BaseDB):
  def __init__(self, paper_list):
    super(PaperDB, self).__init__(paper_list)

def read_paperdb(fname):
  # Produces Unicode strings.
  with open(fname, "rb") as f:
    papers_raw = json.load(f)

  papers = []
  for p in papers_raw:
    papers.append(Paper(p))
  return PaperDB(papers)

def read_paper_id_list(fname):
  paper_ids = []
  with open(fname, "r") as f:
    for line in f:
      paper_ids.append(int(line.strip()))

  return paper_ids
