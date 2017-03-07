import os
import sys
import re
from collections import defaultdict
from record import Record
from annotation_matcher import get_annotation

'''
Patient Splitter Method
Krista Watkins
Feb 10

This doesn't promise a particular order for the patients. Is there any reason we'd care?
'''
#rx_tagged_section = re.compile("<(\\w+)>(.+?)</\\1>", re.DOTALL)
rx_patient_id = re.compile("<(PATIENT_DISPLAY_ID)>(.+?)</PATIENT_DISPLAY_ID>", re.DOTALL)
rx_record_id = re.compile("<(RECORD_DOCUMENT_ID)>(.+?)</RECORD_DOCUMENT_ID>", re.DOTALL)

def get_file_list(dir, test):
    if "win" in sys.platform:
        dir = re.sub(r"\\|/", re.escape(os.sep), dir)
    else:
        dir = re.sub(r"\\|/", os.sep, dir)
    dir = dir.rstrip(os.sep)
    if not test:
        return [os.sep.join((dir, f)) for f in os.listdir(dir) if f.endswith("train.txt")]
    else:
        return [os.sep.join((dir, f)) for f in os.listdir(dir) if f.endswith("test.txt")]

def get_record_id(record):
    patient_id_match = rx_patient_id.search(record)
    record_id_match = rx_record_id.search(record)
    if record_id_match:
        id = record_id_match.group(2).strip("\n")
        if id != "":
            return id
    if patient_id_match:
        id = patient_id_match.group(2).strip("\n")
        if id != "":
            return id

    sys.stderr.write("No Id Found for record: " + record[0:160]  + "\n")

def get_records(file_list, test):
    all_patients = []

    for file_name in file_list:
        records = split_records(file_name)

        # Get Record ID. (May be PAT or REC)
        file_records = defaultdict(str)
        for record in records:
            _id = get_record_id(record)
            if _id in file_records:
                sys.stderr.write("Duplicate record ID: " + _id + "\n")
            file_records[_id] += record

        # get the name of the annotations file corresponding to this record file
        file_version = "train" if not test else "test"
        file_id = "_".join(file_name.split(os.sep)[-1].split("_")[1:3])
        annot_file_name = os.sep.join(file_name.split(os.sep)[:-2] + ["Annotations"] + ["annotations_" + file_id + "_" + file_version + ".json"])

        for _id in file_records.keys():
            record = Record(_id, file_records[_id], file_name, get_annotation(_id, annot_file_name))
            all_patients.append(record)

    # Array of all patient strings. May be multiple records for each patient
    return sorted(all_patients, key=lambda r: int(r.rid[3:]))

def split_records(file_name):
    file = open(file_name)
    text = file.read()
    text = "DUMMY " + text
    file.close()

    records = text.split("**PROTECTED[begin]")
    return records[1:] # The first record is "DUMMY " Don't return that one

def load_records(dir, test=False):
    '''
    This is what to call from other programs.
    Takes a string of a directory path and whether or not we want to
        get the training data or the test data.
    Returns a list of record objects
    '''
    return get_records(get_file_list(dir, test), test)

if __name__ == "__main__":
    # Usage: python3 patientSplitter.py dir_name output_file
    files = get_file_list(sys.argv[1])
    # List of Patient strings. The method splits on the opening line,
    # so "**PROTECTED[begin]" is deleted. It'd be easy enough to add back in if necessary
    records = get_records(files, False)
    with open(sys.argv[2], "w") as out_file:
        print(records[0].record)
        for record in records:
            parse = record.parse()
            record.dump(out_file)
