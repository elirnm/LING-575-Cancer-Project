import json

'''
Eli Miller

Contains functions for getting and parsing the data annotations out
of JSON files. Can search through an annotation for a certain term
and can get all the annotations for any given record.
'''

def parse_json(file):
	rids = {} # maps record id -> their annotations
	annots = json.load(open(file))
	for record in annots:
		rids[record] = annots[record]["Annotations"]
	return rids

def get_annotation(rid, file):
	''' Returns the full annotations section for a record.
	Takes a record id and the file where the record is located.
	File should be the path as a string, NOT a file object.
	Returns the annotations section of the json object, as a group of nested dictionaries.
	Returns None if there is no annotation with the given record id.
	'''
	rids = parse_json(file)
	return rids[rid] if rid in rids else None

def search_annotation(annot, search):
	''' Returns the entry for one category in a record's annotation.
	Takes the dictionary representation of the annotation and a search term.
	Returns a string, where each record in annot (e.g. 1, 2, 3) is separated by '~'
	Returns an empty string if the search term is not found anywhere.
	'''
	answers = ""
	for record in annot:
		try:
			answers += annot[record][search] + "~"
		except KeyError:
			pass
	return answers.strip("~")

if __name__ == "__main__":
	# to test: python annotation_matcher.py record_id filename
	import sys
	from pprint import pprint
	a = get_annotation(sys.argv[1], sys.argv[2])
	pprint(a)
