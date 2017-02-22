import json

# we need to decide what we what to get the annotations for in each call
# a whole file? a patient? etc

def parse_json(file):
	rids = {} # maps record id -> their annotations
	annots = json.load(open(file))
	for record in annots:
		rids[record] = annots[record]["Annotations"]
	return rids

def get_annotation(rid, file):
	''' Returns the full annotations section for a patient.
	Takes a record id and the file where the record is located.
	File should be the path as a string, NOT a file object.
	Returns the annotations section of the json object, as a group of nested dictionaries.
	'''
	rids = parse_json(file)
	return rids[rid]

def search_annotation(annot, search):
	''' Returns the entry for one category in a patient's annotation.
	Takes the dictionary representation of the annotation and a search term.
	Returns a list of strings, where each entry is the result from one record in annot (e.g. 1, 2, 3)
	Returns an empty list if the search term is not found anywhere.
	'''
	answers = []
	for record in annot:
		try:
			answers.append(annot[record][search])
		except KeyError:
			pass

if __name__ == "__main__":
	# to test: python annotation_matcher.py patient_id filename
	import sys
	from pprint import pprint
	a = get_annotation(sys.argv[1], sys.argv[2])
	pprint(a)
