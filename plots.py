import re
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import programcommittee
import submissions
import institutions

from colormap_helper import get_colormap

GnBu = get_colormap(plt.cm.GnBu, 5)
Paired = get_colormap(plt.cm.Paired, 5)

FONT_SIZE = 16
def matplotlib_init():
    mpl.rcParams.update({"font.size": FONT_SIZE,
                         "mathtext.default": "regular",
                         "xtick.major.pad": 5,
                         "ytick.major.pad": 5})
    mpl.rc("xtick", labelsize=FONT_SIZE)
    mpl.rc("ytick", labelsize=FONT_SIZE)
    mpl.rc("legend", **{"fontsize": FONT_SIZE-2})

def plot_topic_distribution(paperdb):
  topic_dist = {}
  for paper in paperdb:
    for topic in paper.topics:
      if topic in topic_dist:
        topic_dist[topic] += 1
      else:
        topic_dist[topic] = 1

  hist = np.array([v for v in topic_dist.itervalues()])
  topic_names = [k for k in topic_dist.iterkeys()]
  for i in range(len(topic_names)):
    topic_names[i] = re.sub("\(.*\)", "", topic_names[i]).strip()
  topic_names = np.array(topic_names)

  idx = np.argsort(hist)
  hist = hist[idx]
  topic_names = topic_names[idx]

  fig = plt.figure()
  fig.set_figheight(7)
  fig.set_figwidth(8)
  ax = fig.add_subplot(111)
  x_centers = np.arange(len(hist))
  bar_width = 0.5
  ax.barh(x_centers + bar_width/2, hist, height=bar_width, color=Paired[2])
  ax.set_yticks(x_centers + bar_width)
  ax.set_yticklabels(topic_names, va="center")
  ax.xaxis.grid(True)
  ax.set_axisbelow(True)
  ax.set_xlabel("Number of papers")
  ax.set_ylim(bottom=0, top=len(hist))
  ax.spines["right"].set_visible(False)
  ax.spines["top"].set_visible(False)
  ax.tick_params(axis="x", which="both", bottom="off", top="off")
  ax.tick_params(axis="y", which="both", right="off")

  plt.savefig("plots/topic_distribution.png", bbox_inches="tight")

def get_score_distribution(paperdb, category):
  buckets = np.zeros(5)
  for paper in paperdb:
    for review in paper.reviews:
      score = review.scores[category]
      buckets[score-1] += 1

  return buckets

def plot_overall_merit_score_distribution(paperdb):
  pre_reb_buckets = get_score_distribution(paperdb, "Overall merit")
  post_reb_buckets = get_score_distribution(paperdb, "Post rebuttal overall merit")

  fig = plt.figure()
  ax = fig.add_subplot(111)
  x_centers = np.arange(5) + 1
  bar_width = 0.3
  ax.bar(x_centers, pre_reb_buckets,
         width=bar_width, label="Pre-rebuttal", color=Paired[0])
  ax.bar(x_centers + bar_width, post_reb_buckets,
         width=bar_width, label="Post-rebuttal", color=Paired[1])
  ax.set_xticks(x_centers + bar_width)
  ax.set_xlabel("Overall merit")
  ax.set_xticklabels(x_centers)
  ax.set_ylabel("Score count")
  ax.set_xlim(left=1-bar_width/2)
  ax.spines["right"].set_visible(False)
  ax.spines["top"].set_visible(False)
  ax.tick_params(axis="x", which="both", bottom="off", top="off")
  ax.tick_params(axis="y", which="both", right="off")
  ax.yaxis.grid(True)
  ax.set_axisbelow(True)
  ax.legend(loc=0)

  plt.savefig("plots/score_distribution.png", bbox_inches="tight")

def plot_score_distribution(paperdb, category):
  hist = get_score_distribution(paperdb, category)

  fig = plt.figure()
  ax = fig.add_subplot(111)
  x_centers = np.arange(5) + 1
  bar_width = 0.7
  ax.bar(x_centers, hist,
         width=bar_width, label=category, color=Paired[0])
  ax.set_xticks(x_centers + bar_width/2)
  ax.set_xlabel(category)
  ax.set_xticklabels(x_centers)
  ax.set_ylabel("Score count")
  ax.set_xlim(left=1-bar_width/2)
  ax.spines["right"].set_visible(False)
  ax.spines["top"].set_visible(False)
  ax.tick_params(axis="x", which="both", bottom="off", top="off")
  ax.tick_params(axis="y", which="both", right="off")
  ax.yaxis.grid(True)
  ax.set_axisbelow(True)
  ax.legend(loc=0)

  category = category.replace(" ", "_")
  plt.savefig("plots/%s_distribution.png" % category, bbox_inches="tight")

def plot_conflicts_per_paper(paperdb, pcdb):
  main_pc_conflict_data = []
  total_pc_conflict_data = []
  for paper in paperdb:
    conflicts = paper.pc_conflicts
    num_main_pc_conf = 0
    num_total_pc_conf = len(conflicts)
    for conf in conflicts:
      if not conf.is_epc:
        num_main_pc_conf += 1
    main_pc_conflict_data.append(num_main_pc_conf)
    total_pc_conflict_data.append(num_total_pc_conf)

  max_conflicts = np.max(total_pc_conflict_data)
  print "Average main PC conflicts per paper: %f" % (np.mean(main_pc_conflict_data))
  print "Average total PC conflicts per paper: %f" % (np.mean(total_pc_conflict_data))
  print "Max conflicts: %d" % max_conflicts

  bin_max = 65
  bins = np.arange(0, bin_max, 5)

  main_pc_hist, main_pc_edges = np.histogram(
      main_pc_conflict_data, bins=bins)
  total_pc_hist, total_pc_edges = np.histogram(
      total_pc_conflict_data, bins=bins)

  fig = plt.figure()
  ax = fig.add_subplot(111)
  x_centers = np.array(bins)
  bar_width = 0.3 * 5  # 5 == bin_width
  ax.bar(x_centers[:len(main_pc_hist)], main_pc_hist,
         width=bar_width, label="Main PC", color=Paired[0])
  ax.bar(x_centers[:len(total_pc_hist)] + bar_width, total_pc_hist,
         width=bar_width, label="PC + EPC", color=Paired[1])
  ax.set_xticks(x_centers[:-1] + bar_width)
  ax.set_xlabel("Number of conflicts")
  ax.set_ylabel("Number of papers")
  ax.spines["right"].set_visible(False)
  ax.spines["top"].set_visible(False)
  ax.tick_params(axis="x", which="both", bottom="off", top="off")
  ax.tick_params(axis="y", which="both", right="off")
  ax.yaxis.grid(True)
  ax.set_axisbelow(True)
  ax.set_xlim(left=-bar_width)

  xticklabels = []
  for i in range(len(main_pc_edges)-1):
    xticklabels.append("%d-%d" % (main_pc_edges[i], main_pc_edges[i+1]))
  xticklabels.append("%d+" % main_pc_edges[-1])
  ax.set_xticklabels(x_centers)
  ax.legend(loc=0)

  plt.savefig("plots/conflict_distribution.png", bbox_inches="tight")

def plot_average_score_distribution(
      paperdb, discuss_list, online_accept_list, prefix="post"):
  discuss_average_scores = []
  for paper_id in discuss_list:
    paper = paperdb[paper_id]
    discuss_average_scores.append(paper.get_average_score())

  accept_average_scores = []
  for paper_id in online_accept_list:
    paper = paperdb[paper_id]
    accept_average_scores.append(paper.get_average_score())

  print "Average Friday:", np.mean(discuss_average_scores)
  print "Average Saturday:", np.mean(accept_average_scores)

  discuss_average_scores = np.array(discuss_average_scores)
  accept_average_scores = np.array(accept_average_scores)

  bins = np.arange(2.0, 5.0, 0.2)
  d_hist, d_edges = np.histogram(discuss_average_scores, bins=bins)
  a_hist, a_edges = np.histogram(accept_average_scores, bins=bins)

  fig = plt.figure()
  ax = fig.add_subplot(111)
  x_centers = np.arange(len(bins))
  bar_width = 0.3
  ax.bar(x_centers[1:], d_hist, label="Friday",
         width=bar_width, color=Paired[0])
  ax.bar(x_centers[1:] + bar_width, a_hist,
         label="Saturday", width=bar_width, color=Paired[1])
  ax.set_xticks(x_centers[1:] + bar_width)
  ax.set_xticklabels(d_edges[1:], fontsize=14)
  ax.set_xlabel("Average score")
  ax.set_ylabel("Number of papers")
  ax.spines["right"].set_visible(False)
  ax.spines["top"].set_visible(False)
  ax.tick_params(axis="x", which="both", bottom="off", top="off")
  ax.tick_params(axis="y", which="both", right="off")
  ax.yaxis.grid(True)
  ax.set_axisbelow(True)
  ax.set_xlim(left=-bar_width)
  ax.legend(loc=0)

  plt.savefig("plots/%s_average_score_distribution.png" % prefix,
              bbox_inches="tight")

def plot_pc_meeting(paperdb, pcdb, instdb):
  matplotlib_init()
  plot_topic_distribution(paperdb)
  plot_overall_merit_score_distribution(paperdb)
  plot_score_distribution(paperdb, "Reviewer expertise")
  plot_score_distribution(paperdb, "Novelty")
  plot_conflicts_per_paper(paperdb, pcdb)

  friday_papers = submissions.read_paper_id_list(
      "data/friday_papers_final.txt")
  saturday_papers = submissions.read_paper_id_list(
      "data/saturday_papers_final.txt")
  friday_online_accept = submissions.read_paper_id_list(
      "data/friday_online_accept.txt")
  saturday_online_accept = submissions.read_paper_id_list(
      "data/saturday_online_accept.txt")

  all_discuss_papers = friday_papers + saturday_papers
  all_online_accept = friday_online_accept + saturday_online_accept

  # plot_average_score_distribution(
  #     paperdb, friday_papers, friday_online_accept, "friday_post")
  # plot_average_score_distribution(
  #     paperdb, saturday_papers, saturday_online_accept, "saturday_post")
  plot_average_score_distribution(
      paperdb, friday_papers, saturday_papers, "comparison_post")
  plot_average_score_distribution(
      paperdb, friday_papers + friday_online_accept,
      saturday_papers + saturday_online_accept, "comparison_oa_post")
  # plot_average_score_distribution(
  #     paperdb, all_discuss_papers, all_online_accept, "all_post")
