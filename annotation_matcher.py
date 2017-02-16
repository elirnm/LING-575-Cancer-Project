import record
import json

def get_annotation(patient):
	text = open(patient.file).readline()
	struct = json.JSONDecoder().decode(text)
	print(struct)

if __name__ == "__main__":
	import sys
	pat = record.Record(1, "", sys.argv[1])
	get_annotation(pat)
