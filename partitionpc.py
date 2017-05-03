# Partition the PC into Friday and Saturday Groups.
#
# Strategies: random and smart.

import random
import re
import unicodecsv as csv
import numpy as np

FRIDAY_TAG = "PC_Friday"
SATURDAY_TAG = "PC_Saturday"
BOTH_TAG = "PC_Both"
EITHER_TAG = "PC_Either"

def count_topics(group):
  """ Produce the distribution of topics from this group of PC members. """
  topics_by_pc = {}
  for member in group:
    for topic in member.topics:
      if not topic in topics_by_pc:
        topics_by_pc[topic] = 1
      else:
        topics_by_pc[topic] += 1
  return topics_by_pc

def normalize_topic_distribution(dist, total):
  """ Normalize topic distribution to percentage of total. """
  normalized = {}
  for topic in dist.iterkeys():
    normalized[topic] = 100.0 * dist[topic] / total[topic]
  return normalized

def compute_combined_score(friday, saturday, total):
  """ Compute score based on both groups simultaneously.

  Score is equal to the sum of the absolute value of differences.
  """
  friday_topics = count_topics(friday)
  saturday_topics = count_topics(saturday)
  score = 0
  for topic in friday_topics.iterkeys():
    diff = abs(friday_topics[topic] - saturday_topics[topic])
    score += diff
  return score

def compute_interday_diff(friday, saturday):
  friday_topics = count_topics(friday)
  saturday_topics = count_topics(saturday)
  diff = [(friday_topics[t] - saturday_topics[t], t) for t in friday_topics.iterkeys()]
  diff.sort(key=lambda v:v[0], reverse=True)
  sorted_diffs = [k[0] for k in diff]
  sorted_percents = np.abs(np.array(sorted_diffs).astype(float))
  sorted_percents = sorted_percents / np.sum(sorted_percents)
  sorted_names = [k[1] for k in diff]
  return sorted_names, sorted_percents, sorted_diffs

def compute_distribution_score(group, total):
  """ Score is distance from a flat distribution of 50%.

  Args:
    group: A list of PC members.
    total: Topic distribution from complete PC.

  Return:
    Score.
  """
  topics = count_topics(group)
  normalized = normalize_topic_distribution(topics, total)

  score = 0
  for value in normalized.itervalues():
    score += abs(value - 50)
  return score

def flip(prob):
  return random.random() < prob

def merge_groups_random(friday, saturday, either, both):
  # Members of either go into one of the other with probability 1/2.
  coinflips = [flip(0.5) for i in range(len(either))]
  for i, coinflip in enumerate(coinflips):
    if i:
      friday.append(either[i])
    else:
      saturday.append(either[i])

  # Members of both are added to balance number of PC members.
  for member in both:
    prob = len(friday)/float(len(friday) + len(saturday))
    if flip(0.3):
      friday.append(member)
      saturday.append(member)
    else:
      if flip(1-prob):
        friday.append(member)
      else:
        saturday.append(member)

  return friday, saturday

def find_best_merging_random(friday, saturday, either, both, total_topics):
  """ Merge either and both into friday or saturday.

  Either can only go into one or the other. Both could go into both. The decisions
  are based on straight probabilities of uniformly distributed random numbers.
  """
  X = 100000
  min_score = 10000000
  best_dist = ()
  for i in range(X):
    # Merge groups X times and find the best distribution.
    merged_friday = [e for e in friday]
    merged_saturday = [e for e in saturday]

    merge_groups_random(merged_friday, merged_saturday, either, both)
    total_score = compute_combined_score(merged_friday, merged_saturday, total_topics)
    if total_score <= min_score:
      min_score = total_score
      best_dist = (merged_friday, merged_saturday)
      print min_score

  return best_dist

def get_random_qualifying_pc_member(group, topic):
  qualifying_pc_members = [member for member in group
                           if topic in member.topics]
  if len(qualifying_pc_members) == 0:
    return None
  return np.random.choice(qualifying_pc_members)

def merge_groups_smart(friday, saturday, either, both):
  """ Smart(er) merging strategy.

  While we still have PC members in 'either' or 'both':
    - Find the topics that are most off-balance in the current distribution.
    - Sample from this distribution, so that the most off balance topic is most
      likely, but not guaranteed to be selected.
    - For each topic, find the list of PC members whose topics include this
      topic.
    - Randomly select a PC member from this list.
    - If the difference is negative, add it to Friday; otherwise, add it to Saturday

  """
  names, percents, diffs= compute_interday_diff(friday, saturday)
  while len(either) > 0 or len(both) > 0:
    # Using this difference as a distribution, draw a random number.
    p = np.random.choice(np.arange(len(diffs)), p=percents)

    # The selected difference.
    target_diff = diffs[p]
    # This selection is the topic we will look for in either or both.
    target_topic = names[p]

    if target_diff < 0:
      dest = friday
    else:
      dest = saturday

    # Special case
    if target_topic.upper().startswith("STORAGE"):
      dest = saturday
    # Select from either first, then both.
    if len(either) > 0:
      selection = get_random_qualifying_pc_member(either, target_topic)
      if not selection:
        # If a member was not found, remove this topic from consideration and
        # try again.
        del names[p]
        diffs = np.delete(diffs, p)
        if len(diffs) == 0:
          # If no topics are remaining, assign the remaining members
          # to groups at random, preferring the shorter list.
          for member in either:
            prob = len(friday)/float(len(friday) + len(saturday))
            if flip(1-prob):
              friday.append(member)
            else:
              saturday.append(member)
          either = []
        else:
          # Redistribute probability of removed topic among the rest.
          prob = percents[p]
          percents = np.delete(percents, p)
          percents += prob/len(percents)
          continue
      else:
        # Based on sign of the difference, put into the appropriate list.
        dest.append(selection)
        either.remove(selection)
    elif len(both) > 0:
      # For members in both, add them to both days with some probability.
      selection = get_random_qualifying_pc_member(both, target_topic)
      if not selection:
        # If a member was not found, remove this topic from consideration and
        # try again.
        del names[p]
        diffs = np.delete(diffs, p)
        if len(diffs) == 0:
          # If no topics are remaining, add the remainder to both groups.
          friday.extend(both)
          saturday.extend(both)
          break
        # Redistribute probability of removed topic among the rest.
        prob = percents[p]
        percents = np.delete(percents, p)
        percents += prob/len(percents)
        continue
      if flip(0.4):
        friday.append(selection)
        saturday.append(selection)
      else:
        dest.append(selection)
      both.remove(selection)
    names, percents, diffs = compute_interday_diff(friday, saturday)

  return friday, saturday

def find_best_merging_smart(friday, saturday, either, both, total_topics):
  """ Actively try to bring distributions into balance. """
  num_topics = len(total_topics)

  min_score = 10000
  X = 10000  # Num of trials
  best_dist = ()
  for i in range(X):
    # Make a copy of all arrays.
    merged_friday = [e for e in friday]
    merged_saturday = [e for e in saturday]
    temp_both = [e for e in both]
    temp_either = [e for e in either]

    merged_friday, merged_saturday = merge_groups_smart(
        merged_friday, merged_saturday, temp_either, temp_both)
    score = compute_combined_score(merged_friday, merged_saturday, total_topics)
    if score < min_score:
      min_score = score
      best_dist = (merged_friday, merged_saturday)
      print min_score

  return best_dist

def partition_pc(pcdb, strategy="random"):
  """ Partition the PC into Friday and Saturday groups. """
  friday = []
  saturday = []
  either = []
  both = []

  total_topics = count_topics(pcdb)

  for member in pcdb:
    if FRIDAY_TAG in member.tags:
      friday.append(member)
    elif SATURDAY_TAG in member.tags:
      saturday.append(member)
    elif EITHER_TAG in member.tags:
      either.append(member)
    elif BOTH_TAG in member.tags:
      both.append(member)

  if strategy == "random":
    merged_friday, merged_saturday = find_best_merging_random(
        friday, saturday, either, both, total_topics)
  else:
    merged_friday, merged_saturday = find_best_merging_smart(
        friday, saturday, either, both, total_topics)

  return merged_friday, merged_saturday

def print_partition(group, label, pcdb):
  topics_dist = count_topics(group)
  total_topics = count_topics(pcdb)

  # Print in sorted fashion.
  topic_names = [t for t in topics_dist.iterkeys()]
  topic_names.sort()
  topic_names_lengths = [len(t) for t in topic_names]
  longest_topic_name_len = max(topic_names_lengths)
  indent = longest_topic_name_len + 3

  with open("%s_group.txt" % label, "w") as f:
    f.write("=========\n")
    f.write("Number of %s confident PC members by topic\n=========\n" % label)
    for topic in topic_names:
      num = topics_dist[topic]
      add_spaces = indent - len(topic)
      f.write("%s:%s%d (%2.2f)\n" % (
          topic, add_spaces*' ', num, 100.0*num/total_topics[topic]))

    f.write("=========\n")
    f.write("PC members (%d):\n=========\n" % len(group))
    for member in group:
      f.write("%s\n" % (member.name))

def print_partition_diff(group1, group2, pcdb):
  topics_dist1 = count_topics(group1)
  topics_dist2 = count_topics(group2)
  total_topics = count_topics(pcdb)

  # Print in sorted fashion.
  topic_names = [t for t in topics_dist1.iterkeys()]
  topic_names.sort()
  topic_names_lengths = [len(t) for t in topic_names]
  longest_topic_name_len = max(topic_names_lengths)
  indent = longest_topic_name_len + 3

  with open("diff_group.txt", "w") as f:
    f.write("=========\n")
    f.write("Difference in topics per day.\n=========\n")
    for topic in topic_names:
      num = topics_dist1[topic] - topics_dist2[topic]
      percent = float(num)/total_topics[topic]
      add_spaces = indent - len(topic)
      f.write("%s:%s%d (%2.2f)\n" % (topic, add_spaces*' ', num, percent))

def verify_partition(group, tag):
  """ Verify that all members in this group belong to the correct tag. """
  for member in group:
    assert(tag in member.tags or
           BOTH_TAG in member.tags or
           EITHER_TAG in member.tags)

  print "%s group verified" % tag

def verify_all_pc_members_present(friday, saturday, pcdb):
  check = set(friday) | set(saturday)
  for member in pcdb:
    if not member.is_epc and not member in check:
      print member, "missing!"

def read_partition_file(fname, pcdb):
  group = []
  # idre = re.compile("^[0-9]+(?=:)")
  started = False
  with open(fname, "r") as f:
    for line in f:
      if not line.startswith("PC members") and not started:
        continue
      elif not started:
        started = True
        f.next()
        line = f.next()
      if started:
        pcname = line.strip()
        pcid = pcdb.getid(pcname)
        group.append(pcdb[pcid])
  return group

def print_pc_members_by_topic(pcdb, outfname):
  topics = count_topics(pcdb)
  with open(outfname, "w") as f:
    for topic in topics:
      group = [member for member in pcdb if topic in member.topics]
      f.write("Topic:" + topic + "\n")
      for member in group:
        f.write("  " + member +  member.tags + "\n")

def print_topics_by_pc_members(group, outfname):
  """ Print the topics of expertise by (E)PC members. """
  with open(outfname, "w") as f:
    for pcmember in group:
      if not pcmember.is_epc:
        f.write(pcmember.name.encode("utf-8") + "\n")
        if len(pcmember.topics) == 0:
          f.write("  None\n")
        else:
          for topic in pcmember.topics:
            f.write("  " + topic + "\n")
        f.write("==============\n")

def print_topic_pc_member_spreadsheet(pcdb, outfname):
  """ Print a spreadsheet of EPC members and areas of expertise. """
  topics = count_topics(pcdb)
  output = []
  with open(outfname, "w") as f:
    row = [""]
    for topic in topics.iterkeys():
      row.append(topic)
    output.append(row)
    for pcmember in pcdb:
      if pcmember.is_epc:
        continue
      row = []
      row.append(pcmember.name)
      for topic in topics.iterkeys():
        if topic in pcmember.topics:
          row.append("X")
        else:
          row.append("")
      output.append(row)

    writer = csv.writer(f, delimiter=",")
    for row in output:
      writer.writerow(row)
