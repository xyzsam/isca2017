# -*- coding: utf-8 -*-

import re
import codecs

import base

class Review(base.BaseObj):
  def __init__(self, name):
    super(Review, self).__init__()
    self.name = name
    # Assume the name is of the form 175B, where 175 is the paper id and B is
    # the second review.
    self.paper_id = int(name[:-1])
    review_num = ord(name[-1]) - ord('A')
    self.reviewer = ""
    self.reviewer_email = ""

    # We never have more than 10 reviews. This is effectively a decimal
    # concatentation of paper id and number.
    self.id = self.paper_id * 10 + review_num

    # These keys are designed to match what HotCRP dumps in the review text.
    self.scores = {
        "Post rebuttal overall merit": 0,
        "Overall merit": 0,
        "Novelty": 0,
        "Writing quality": 0,
        "Reviewer expertise": 0}

    # Ignore review text for now. We don't need it.
    self.paper_summary = ""
    self.strengths = ""
    self.weaknesses = ""
    self.comments_to_authors = ""
    self.post_reb_comments_to_authors = ""
    self.questions_for_authors = ""
    self.comments_to_PC = ""

  def set_scores(self, scores):
    assert(isinstance(scores, dict))
    self.scores.update(scores)

  def fix_missing_scores(self):
    postRebScore = "Post rebuttal overall merit"
    if self.scores[postRebScore] == 0:
      self.scores[postRebScore] = self.scores["Overall merit"]

  def print_offline_form(self, form_file):
    print >>form_file, "==+== ====================================================================="
    print >>form_file, "==+== Begin Review"
    print >>form_file, "==+== Version 20"
    print >>form_file, "==+== Reviewer:", self.reviewer, "<%s>" % self.reviewer_email
    print >>form_file, ""
    print >>form_file, "==+== Paper #%d" % self.paper_id
    print >>form_file, "==+== Review Readiness"
    print >>form_file, ""
    print >>form_file, "Ready"
    print >>form_file, ""
    print >>form_file, "==+== A. Post rebuttal overall merit (hidden from authors)"
    print >>form_file, self.scores["Post rebuttal overall merit"]
    print >>form_file, "==+== B. Overall merit"
    print >>form_file, self.scores["Overall merit"]
    print >>form_file, "==+== C. Novelty"
    print >>form_file, self.scores["Novelty"]
    print >>form_file, "==+== D. Writing quality"
    print >>form_file, self.scores["Writing quality"]
    print >>form_file, "==+== E. Reviewer expertise"
    print >>form_file, self.scores["Reviewer expertise"]
    # print >>form_file, "==+== F. Paper summary"
    # print >>form_file, self.paper_summary
    # print >>form_file, "==+== G. Strengths"
    # print >>form_file, self.strengths
    # print >>form_file, "==+== H. Weaknesses"
    # print >>form_file, self.weaknesses
    # print >>form_file, "==+== I. Comments to authors"
    # print >>form_file, self.comments_to_authors
    # print >>form_file, u"==+== J. Questions for authors’ response"
    # print >>form_file, self.questions_for_authors
    # print >>form_file, "==+== K. Comments to PC (hidden from authors)"
    # print >>form_file, self.comments_to_PC
    # print >>form_file, "==+== L. Post rebuttal comments to authors (hidden from authors)"
    # print >>form_file, self.post_reb_comments_to_authors
    # print >>form_file, "==+== Scratchpad"
    print >>form_file, "==+== End Review"
    print >>form_file, ""

  def __unicode__(self):
    scores = tuple(v for v in self.scores.itervalues())
    return u"Review({0}, scores={1})".format(self.name, str(scores))

  def __str__(self):
    return unicode(self).encode('utf-8')

  def __repr__(self):
    return str(self)

class ReviewDB(base.BaseDB):
  def __init__(self, review_list):
    super(ReviewDB, self).__init__(review_list)

def read_reviewdb(fname):
  REVIEW_BEGIN = "ISCA 2017 Review #"
  REVIEW_SUMMARY = "===== Paper summary ====="
  REVIEW_STRENGTHS = "===== Strengths ====="
  REVIEW_WEAKNESSES = "===== Weaknesses ====="
  REVIEW_AUTHOR_COMMENTS = "===== Comments to authors ====="
  REVIEW_AUTHOR_QUESTIONS = u"===== Questions for authors’ response ====="
  REVIEW_PC_COMMENTS = "===== Comments to PC ====="
  REVIEW_POST_REB_COMMENTS = "===== Post rebuttal comments to authors ====="
  REVIEW_BIG_SEPARATOR = "======================="
  REVIEW_MEDIUM_SEPARATOR = "====="
  REVIEW_SMALL_SEPARATOR = "----------"
  REVIEWER = "Reviewer:"
  review_id_re = re.compile("(?<=ISCA 2017 Review #)[0-9A-Z]+")
  reviewer_re = re.compile("(?<=Reviewer: ).*")
  # Score lines contain the category name, the score, and the description.
  score_re = re.compile("(\w[\w\s,-]+|\d+)")
  review_list = []
  with codecs.open(fname, encoding="utf-8") as review_file:
    current_review = None
    while True:
      line = review_file.readline()
      if not line:
        break

      # Find the review id.
      if not current_review and REVIEW_BEGIN in line:
        review_id = re.findall(review_id_re, line)[0]
        current_review = Review(review_id)
      else:
        continue

      print "Current review:", review_id

      # Get the reviewer name.
      while not REVIEWER in line:
        line = review_file.readline()
      reviewer = re.findall(reviewer_re, line)[0].strip()
      reviewer_email = re.findall("(?<=<).*(?=>)", reviewer)
      # Remove the email address if it has one.
      reviewer = re.sub("<.*>", "", reviewer).strip()
      if reviewer_email:
        current_review.reviewer_email = reviewer_email[0]
      else:
        # Reviewer email might be on the next line
        line = review_file.readline().strip()
        reviewer_email = re.findall("(?<=<).*(?=>)", line)
        if reviewer_email:
          current_review.reviewer_email = reviewer_email[0]
        else:
          print "Review %s is missing reviewer email" % review_id
      current_review.reviewer = reviewer

      # Get the review scores.
      line = review_file.readline().strip()
      while not line or REVIEW_SMALL_SEPARATOR in line:
        line = review_file.readline().strip()

      scores = {}
      while line:
        score_match = re.findall(score_re, line)
        if len(score_match) == 3:
          score_type = score_match[0]
          score_val = int(score_match[1])
          scores[score_type] = score_val
        line = review_file.readline().strip()

      current_review.set_scores(scores)
      current_review.fix_missing_scores()

      # Get the review text.
      while not REVIEW_BIG_SEPARATOR in line:
        if not line:
          line = review_file.readline().strip()
          continue
        if REVIEW_MEDIUM_SEPARATOR in line:
          # We found a review field.
          review_field_name = line
          # Read the rest of the field.
          line = review_file.readline().strip()
          review_content = []
          while (not REVIEW_MEDIUM_SEPARATOR in line):
            review_content.append(line)
            line = review_file.readline().strip()
          review_content_str = "\n".join(review_content)

          if review_field_name == REVIEW_SUMMARY:
            current_review.paper_summary = review_content_str
          elif review_field_name == REVIEW_STRENGTHS:
            current_review.strengths = review_content_str
          elif review_field_name == REVIEW_WEAKNESSES:
            current_review.weaknesses = review_content_str
          elif review_field_name == REVIEW_AUTHOR_QUESTIONS:
            current_review.questions_for_authors = review_content_str
          elif review_field_name == REVIEW_AUTHOR_COMMENTS:
            current_review.comments_to_authors = review_content_str
          elif review_field_name == REVIEW_PC_COMMENTS:
            current_review.comments_to_PC = review_content_str
          elif review_field_name == REVIEW_POST_REB_COMMENTS:
            current_review.post_reb_comments_to_authors = review_content_str
          else:
            print "Unknown field", review_field_name
        else:
          line = review_file.readline().strip()

      review_list.append(current_review)
      current_review = None

  return ReviewDB(review_list)

def merge_with_paperdb(reviewdb, paperdb):
  for review in reviewdb:
    paperdb[review.paper_id].reviews.append(review)
