from html import HTML
from itertools import groupby
from numpy import array, average, linalg, var
from operator import itemgetter
import csv
import webbrowser
import os

positions = {}
headers = ["Errors", "Start Time", "End Time"]
displayNames = {
  "swaying": "Swaying",
  "handsonhips": "Hands on Hips",
  "turnback": "Turn Back to Face Slides",
  "gesturing": "Gesture",
  "armscrossed": "Arms Crossed",
  "legscrossed": "Legs Crossed",
  "rocking": "Rocking Back and Forth",
  "handsonface": "Hands on Face",
  "legtwitch": "Leg Twitch"
}
errors = []

def read_positions(filename):
  with open(filename, 'rb') as f:
      reader = csv.reader(f.read().splitlines())
      count = 0
      for row in reader:
        if count == 0:
          header = row
          for col in row:
            positions[col] = []
        else:
          colnum = 0
          for col in row:
            positions[header[colnum]].append(float(col))

            colnum += 1
        count += 1
  return positions

def get_positions():
  return positions

# Actually, instead of cutting positions, we just discount those values and use them as padding for sliding window instead?
def get_cut_positions():
  end_buffer = 100
  start_buffer = 50
  cut = {}
  for key in positions:
    cut[key] = positions[key][start_buffer:-end_buffer]
  return cut

def process_positions(filename):
  read_positions(filename)
  pos = get_cut_positions()
  numPos = len(pos['timestamp'])
  errors = {"swaying": [],
            "turnback": [],
            "gesturing": [],
            "handsonhips": [],
            "armscrossed": [], 
            "legscrossed": [],
            "rocking": [],
            "handsonface": []}
  window = 80
  for i in range(numPos):
    start = i
    snapshot = get_snapshot(start, window, pos)
    results = analyze_snapshot(snapshot)
    for key in results:
      if results[key]:
        errors[key].append(i)

  formatted_errors = filter_report(errors, pos)

  html_string = create_html(formatted_errors)
  return html_string

def get_snapshot(start, window, pos):
  cut = {}
  for key in pos:
    cut[key] = pos[key][start:start+window]
  return cut

def analyze_snapshot(snapshot):
  report = {}
  # Swaying Detector
  if (getVar("headx", snapshot) > 2000) and (getVar("torsox", snapshot) > 2000) and (max(getVar("leftshoulderz", snapshot), getVar("rightshoulderz", snapshot)) < 1000):
    report["swaying"] = True


  # Turn back to face slides detector
  if (getVar("leftshoulderz", snapshot) > 2000) or (getVar("rightshoulderz", snapshot) > 2000):
    if abs(average(snapshot["leftshoulderz"]) - average(snapshot["rightshoulderz"])) >= 50:
      report["turnback"] = True

  # Hands on hips
  # Checks distance from hands to hips, as well as movement in hands in the y direction
  # TODO: needs to be more specific!! Add in more features --> elbows? x axis?
  rhandhipdist = getDist('righthand', 'righthip', snapshot)
  lhandhipdist = getDist('lefthand', 'lefthip', snapshot)
  if (rhandhipdist < 150 and getVar('righthandy', snapshot) < 50) or (lhandhipdist < 150 and getVar('lefthandy', snapshot) < 50):
    report["handsonhips"] = True

  # Gesturing
  if all_greater_than(['lefthand', 'righthand'], 1000, snapshot):
    report["gesturing"] = True

  # Arms Crossed
  rhand_lelbowdist = getDist('righthand', 'leftelbow', snapshot)
  lhand_relbowdist = getDist('lefthand', 'rightelbow', snapshot)
  if (rhand_lelbowdist < 250) or (lhand_relbowdist < 250) or (average(snapshot["righthandx"]) - average(snapshot["lefthandx"]) < 0):
  # if righthand pos - lefthand pos < -100?
    report["armscrossed"] = True

  # Legs Crossed


  # Rocking
  # Maybe get more specific?
  if (getVar("torsoz", snapshot) > 2000) and (abs(average(snapshot["leftshoulderz"]) - average(snapshot["rightshoulderz"])) < 50):
    report["rocking"] = True

  rhandface = getDist('head', 'righthand', snapshot)
  lhandface = getDist('head', 'lefthand', snapshot)
  if (rhandface < 300) or (lhandface < 300):
    report['handsonface'] = True

  # if (max(snapshot["leftkneez"]) - average(snapshot["leftkneez"])) > 200:
  #   report['legtwitch'] = True

  return report

def getVar(part, snapshot):
  return var(snapshot[part])

def getDist(firstpart, secondpart, snapshot):
  firstpoint = array((average(snapshot[firstpart + 'x']), average(snapshot[firstpart + 'y']), average(snapshot[firstpart + 'z'])))
  secondpoint = array((average(snapshot[secondpart + 'x']), average(snapshot[secondpart + 'y']), average(snapshot[secondpart + 'z'])))

  return linalg.norm(firstpoint-secondpoint)

# Helper function for analysis
def all_greater_than(parts, threshold, snapshot):
  for part in parts:
    directions = ['x', 'y', 'z']
    for direction in directions:
      part_w_direction = part + direction
      if var(snapshot[part_w_direction]) < threshold:
        return False
  return True

# Helper function?
def one_less_than(parts, threshold):
  for part in parts:
    if part < threshold:
      return True
  return False

def filter_report(report, pos):
  formatted_report = {}

  for error in report:
    formatted_errors = []
    times = report[error]
    grouped_times = [map(itemgetter(1), g) for k, g in groupby(enumerate(times), lambda (i,x):i-x)]

    for time in grouped_times:
      if len(time) > 1:
        original_times = pos['timestamp']
        formatted_error = {"start": format(original_times[time[0]]),
                           "end": format(original_times[time[-1]])}
        formatted_errors.append(formatted_error)

    formatted_report[error] = formatted_errors
  print formatted_report
  return formatted_report

def format(time):
  starttime = positions['timestamp'][0]
  newtime = time - starttime
  return int(newtime/1000)

def create_html(formatted_errors):
  h = HTML()
  for error in formatted_errors:
    t = h.table
    header = t.tr
    header.th("Detected")
    header.th("Start")
    header.th("End")
    formatted_error = formatted_errors[error]
    if len(formatted_error) > 0:
      for group in formatted_error:
        r = t.tr
        r.td(displayNames[error])
        r.td(str(group["start"]))
        r.td(str(group["end"]))
    else:
      r = t.tr
      r.td(displayNames[error])
      r.td("None detected!")

  return str(h)

def write_html(html_string):
  HTMLFILE = 'report.html'
  f = open(HTMLFILE, 'w')
  header = """
    <head>
      <link rel="stylesheet" type="text/css" href="speechBuddy.css">
    </head>
  """
  title = "<h1>SpeechBuddy Feedback Report</h1>"
  html = header + title + html_string
  f.write(html)
  f.close()
  return

def launch_page():
  webbrowser.open("file:///" + os.path.abspath("report.html"), new=2)


if __name__ == "__main__":
  html_string = process_positions("positions.csv")
  write_html(html_string)
  launch_page()