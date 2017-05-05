ISCA 2017 Conflict/Paper Management
===================================

This is a set of scripts to automate various tasks in managing a conference run
through HotCRP. Functions include:

* PC conflict identification for submissions.
* Partitioning of PC members into two days (for a 2-day PC meeting).
* Paper review assignments preferences.
* Parsing of paper reviews.
* Various plotting functions.

Expect varying degrees of hard-codedness here, based on how rushed I was at the
time to produce a result :)

Requirements
------------

* fuzzywuzzy - a Python fuzzy matching library. Available here:
  https://github.com/seatgeek/fuzzywuzzy
* A HotCRP submissions database dump in JSON format.
* A HotCRP PC member information dump in CSV format.
* A manually constructed list of institutions and common aliases. I've provided
  the one I've made (data/institutions.csv) but you may need to make additional
  changes.
* Lots of patience.


Getting the required information
--------------------------------------------

HotCRP submissions database dump:
  - Search for all submitted papers.
  - Scroll to the very bottom of the long list.
  - Select all papers
  - Download: JSON.
  - Place the downloaded file into data/isca2017db-data.json.

HotCRP PC info dump:
  - Go to Users -> Program committee.
  - Scroll to the bottom
  - Select all PC members
  - Download: PC info.
  - Place the downloaded file into data/isca2017db-pcinfo.csv

Institutions list:
  - This is a CSV file of institutions that are associated with the conference
    submissions.
  - Each line contains different ways of expressing the same institution (e.g.
    UVA/University of Virginia).
  - The first element of each line is considered the "canonical" name. These
    scripts will use the canonical name whenever printing output.
  - Every name in the list must be unique (or mismatches could ocurr).
  - See data/institutions.csv for an example. You will probably need to add more
    entries to this list.

Before running
--------------

Create the following directories:
- data/
- results/
- correct/
- paperpartitions/
- pcpartitions/
- plots/

You might not use all of these but the scripts might assume one of them exists.

PC conflict identification
--------------------------

Although submissions are supposed to mark all PC members they have conflicts
with in a structured way by checking off names from a list, in practice this
does not happen for several reasons.

1. Authors do not mark all PC members that have an institutional conflict.
2. Authors do not notice various changes to the PC.
3. Authors are too lazy to scroll through the long list of PC/EPC.
4. Authors do not realize that some people they were not conflicted with before
   are now conflicted (possibly due to changing institutions).
5. Authors ignore the checkboxes entirely and simply write down names of
   institutions and conflicted people (regardless of whether or not they are on
   the PC) in a free-form textbox.

This last one is particularly annoying. HotCRP gives authors the ability to add
as many collaborators as they have in a free-form text box labeled
"Collaborators". The fact that this is free-form means authors could specify
names of people/institutions in a myriad of different ways, which is why fuzzy
string matching is needed at all (and the reason why PC conflict matching is so
tedious).

To identify as many missing conflicts as possible, we've divided PC conflict
identification into three steps:

  1. Matching individual person names in the free-form "Collaborators" box with
     names of PC members.

     Just a note: This is probably the most time consuming part because it
     requires the most manual work in verifying the output of the conflict
     matching system.

  2. Finding PC members who belong to the same institution as the authors'
     current affliation.

  3. Matching names of institutions in the free-form "Collaborators" box with
     known institutions and finding PC members who also belong to those
     institutions.

# Step 1 #

Run the command:

    python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv mark-collaborators > results/step1_pcconflicts

This command will print out potential conflicted papers for every PC member
using data from the free-form Collaborators box. Output would look something like this:

```
=================================
PC member  0 ## AJAY JOSHI
=================================
1 ## 76 : RAJIV JOSHI  !!! VERIFY !!!
2 ## 100 : AJAY JOSHI
3 ## 100 : AJAY JOSHI
4 ## 100 : - AJAY JOSHI
```

The format is:

```
==================================
PC member   [PC_ID] ## PC_NAME
==================================
[PAPER_ID] ## [FUZZY_SCORE] : [MATCHED STRING]  [!!! VERIFY !!!]
```

where:
  - PC_ID is an internal id for each PC member.
  - PC_NAME is the name of the PC member, obtained from isca2017db-pcinfo.csv
  - PAPER_ID is the HotCRP submission id for a potentially conflicted paper.
  - MATCHED_STRING is a line of text from the free-form text box that closely
    matches the name of the PC member.
  - FUZZY_SCORE is the fuzzy string matching score for the matched string.
  - If FUZZY_SCORE > 70 and < 80, then [!!! VERIFY !!!] is printed. You can
    change these thresholds in main.py:mark_collaborators_on_pc_conflicts().

Review each matched entry in this file and delete any lines that are false
conflicts. You don't need to take out the "VERIFY" part, but it might be good
help you track which ones you have taken care of already. The VERIFY string
is just there to help you spot potential mismatches.

The example shows that "AJAY JOSHI" matched "RAJIV JOSHI" with score 76, which
is above the threshold, but it would not be a correct match. So that line
should be deleted.

People often declare collaborator names along with their respective
institutions, in a myriad of different ways.

  * DAVID WOOD - University of Wisconsin
  * DAVID BROOKS: Harvard
  * AJAY JOSHI, BU
  * JASON MARS (Michigan)

To simplify this mess, I try to strip away as many institution names as I can
so that the fuzzy string matching only needs to worry about people names at
this step. Unfortunately, there are still many cases where my automatic matching
doesn't work (e.g. people have a numbered list of names and institutions, along
with a stated reason for the conflict). In such cases, I just fall back to
manually editing the collaborator text in the JSON dump to make it amenable to
the scripts.

The fuzzy string matching algorithm ignores non-alphanumeric characters. That
is why the last line in the example output contains a dash, but the matching
score was still 100.

While this system works reasonably well, it can miss cases where two people's
names differ by one letter, like "DAVID WENTZLAFF" and "DAVID WENTZLOFF".
VERIFY would not be printed in this case! Also, be on the lookout for Unicode
characters - these can be tricky for the system.

You will probably find some edge cases for certain submissions. I've found that
oftentimes, the simplest way to resolve these is probably just to modify the
data JSON dump directly to make a collaborator name match with the name of a PC
member.

This step is the most time consuming and error prone step. Be sure to get this
right. When you are done, move on to steps 2 and 3.

# Steps 2 and 3 #

Run the command:

    python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv find-conflicts

This command will match PC members with institutional conflicts and add them to
the set of collaborator conflicts identified in Step 1 (using the prepared
step1_pcconflicts file). By default, this will run all the steps of the
conflict matching algorithms at once. When it is done, it will produce a CSV
file that contains *newly found* PC conflicts (not including ones that were
already declared). The CSV file can be uploaded to HotCRP as a batch update.

If you want to run Step 2 and Step 3 separately (and obtain separate update
CSVs), add the flag --separate-steps to the command.

This part will use the institutions.csv file. You will probably find some edge
cases for certain submissions, and the simplest way to resolve those is
probably just to modify the data JSON dump directly to make an institution name
match with a known name (inside institutions.csv).

The update csv subtracts all the originally declared PC conflicts because
HotCRP lets you preview the changes you make during a bulk update before you
commit, so it will show you in a prettier way all the changes you are about to
make. Removing the known conflicts makes the set of changes smaller and easier
to eyeball. If you want a comprehensive list, just comment on the call to
subtract_orig_pc_conflicts() in main.py.

# Finally #

Take that hard earned update.csv and upload it! From now on, you can specify
the path to this update csv with the flag `--existing-update-csv path/to/file`
to automatically reuse this data when running the scripts for other purposes.


PC/Paper partitioning
---------------------

I have a way to automatically partition a PC into two sets for a 2-day meeting
in a way that best balances the self-declared areas of expertise. To use this system,
run the command:

    python main.py data/isca2017db-data.json data/isca2017db-pcinfo.csv data/institutions.csv --existing-update-csv update.csv partition-pc

This will print two files containing the set of PC members for each day.

In order for this to work, the PC chair needs to collect the date preferences for each
PC member and mark each PC member account with the appropriate tag
(PC_Friday/PC_Saturday/PC_Either/PC_Both). "Either" means either day but one
day only, while "Both" means they can attend both days if needed.

Once the PC has been partitioned, you can then partition the papers such that
all the PC members who might review it will be present on the same day. This relies
on the self-declared topics for each submission. The output is an update csv that
adds new tags for each submission marking it as either a Friday or Saturday
paper.  This is just a first-pass analysis - the PC chair still has to go in
and manually assign reviews, as well as potentially change the
automatically-generated assignments.

Helping with paper review assignments
-------------------------------------

These scripts can produce a spreadsheet of papers and PC members with conflicts
marked as "C".  The PC chair can mark up this spreadsheet with a set of scores
from 1-10, where a higher score means a higher preference for a reviewer to
review a particular paper. Then, the scripts can convert this spreadsheet into
an update CSV for HotCRP. The update csvs will contain the preference scores
for each PC member and paper. HotCRP uses this information to then
automatically assign reviewers for each paper.

- Exporting the spreadsheet of conflicts is handled by the function
  export_paper_spreadsheets() inside partitionpapers.py.
- Exporting the update csv of review preferences is handled by the function
  export_review_preferences() inside export2hotcrp.py.

Many of these functions are found in secondary.py and export2hotcrp.py. It might be
simpler for you to study how these functions are written and write your own functions
using the databases that the scripts have assembled thus far (for PC members,
submissions, and institutions), rather than try to rework the existing
functions for your own purposes.  Quite a few of these functions were written
for one-off purposes (e.g. fixing some mistakes in assignments, conflicts,
etc).

This is the point where lots of hard-coded file names are littered around.
You'll need to change these.

Final words
-----------

This is a tedious, error-pone, and manual process. Hopefully these scripts make
your lives a bit easier.  If you have any questions, feel free to ask me.

Good luck!

Sam Xi

slxi1202@gmail.com
