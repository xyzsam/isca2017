# Base database class and other common methods.

from bisect import bisect_left, bisect
from fuzzywuzzy import process, fuzz

def dict_default(dictobj, key, default):
  """ If key exists in dictobj, return the value, otherwise return default. """
  if key in dictobj:
    return dictobj[key]
  return default


class BaseObj(object):
  # Base object to be stored in a database.

  def __init__(self):
    # Required fields in the database.
    self.name = ""
    self.id = -1

    # Raise this flag if there is a data problem that may need to be fixed.
    self.flag = False

  def raise_flag(self):
    self.flag = True
    print u"Flag raised on", self

  def __lt__(self, other):
    return self.name < other.name

class BaseDB(object):
  # Base database class.
  #
  # DBs store an dict of the original objects, keyed by object id, and a sorted
  # list of (name, id) tuples. The list is sorted by the name field and is used
  # to quickly find an exact matching pair and id with binary search.
  #
  # DBs also support fuzzy querying based on the name field of each object. The
  # find_closest() method returns the (name, id) tuple for the closest match.

  def __init__(self, inst_list):
    """ Constructs the orig, names, and pairs members. """
    self.orig = dict([(obj.id, obj) for obj in inst_list])

    all_pairs = []
    all_names = []
    for inst in inst_list:
      all_pairs.append((inst.name, inst.id))
      all_names.append(inst.name)
    all_pairs.sort(key=lambda tup: tup[0])
    all_names.sort()
    self.pairs_ = all_pairs
    self.names_ = all_names

    self.current_ = -1

  def indexof(self, name, lo=0, hi=None):
    """ Search institution db for name x. """
    hi = hi if hi is not None else len(self.names_)  # hi defaults to len(a)
    pos = bisect_left(self.names_, name, lo, hi)  # find insertion position
    pos = (pos if pos != hi and self.names_[pos] == name else -1)  # don't walk off the end
    return pos

  def find_obj_by_attr(self, value, field):
    """ Return the id of the object with the given attribute's value. """
    result = self.find_objs_by_attr(value, field)
    if len(result) == 0:
      return None
    return result[0]

  def find_objs_by_attr(self, value, field):
    """ Get all objects whose attribute is the given value. """
    result = []
    for obj in self.orig.itervalues():
      obj_value = getattr(obj, field)
      if obj_value == value:
        result.append(obj)
    return result

  def getid(self, value, field="name"):
    if field == "name":
      pos = self.indexof(value)
      if pos == -1:
        return -1
      return self.pairs_[pos][1]
    else:
      result = self.find_obj_by_attr(value, field)
      if result:
        return result.id
      return -1

  def find_closest(self, query, scorer=fuzz.ratio):
    result = process.extractOne(query.upper(), self.names_, scorer=scorer)
    if not result:
      return None
    institution = result[0]
    score = result[1]
    pos = self.indexof(institution)
    return {"name": self.pairs_[pos][0],
            "id": self.pairs_[pos][1],
            "score": score }

  def __getitem__(self, id):
    return self.orig[id]

  def __contains__(self, name):
    return self.indexof(name) != -1

  def __iter__(self):
    return self.orig.itervalues()
