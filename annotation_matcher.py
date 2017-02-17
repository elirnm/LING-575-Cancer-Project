import record
import json
from pprint import pprint

# we need to decide what we what to get the annotations for in each call
# a whole file? a patient? etc

def parse_json(file):
	pids = {} # maps patient id -> their annotations
	annots = json.load(open(file))
	# pprint(annots["PAT9"])
	# pprint(annots["PAT9"]["PatientId"])
	for record in annots:
		pid = annots[record]["PatientId"]
		pids[pid] = annots[record]["Annotations"]
		# need to decide here how to deal with patients who have mulitiple records

def get_annotation(patient):
	parse_json(patient.file)

if __name__ == "__main__":
	import sys
	pat = record.Record(1, "", sys.argv[1])
	get_annotation(pat)
