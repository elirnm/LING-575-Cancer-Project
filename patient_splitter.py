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

Usage: python3 recordSplitter.py dir_name output_file

This doesn't promise a particular order for the patients. Is there any reason we'd care?
'''
rx_tagged_section = re.compile("<(\\w+)>(.+?)</\\1>", re.DOTALL)

def get_file_list(dir):
    # this stuff throws an exception for some reason. It should get figured out
    # dir = re.sub(r"\\|/", os.sep, dir)
    # dir = dir.strip(os.sep)
    # print([os.sep.join((dir, f)) for f in os.listdir(dir) if f.endswith(".txt")])
    # return [os.sep.join((dir, f)) for f in os.listdir(dir) if f.endswith(".txt")]

    dir = dir.strip("/")
    return ["/".join((dir, f)) for f in os.listdir(dir) if f.endswith(".txt")]

def get_patient_id(record):
    first_section = rx_tagged_section.search(record)
    if not first_section or first_section.group(1) != "PATIENT_DISPLAY_ID":
        sys.stderr.write("No Patient ID found:\n")
        sys.stderr.write(record)
        return "none"
    else:
        return first_section.group(2).strip("\n")

def get_records(file_list, test):
    all_patients = []

    for file_name in file_list:
        records = split_records(file_name)

        # check for records with matching patient IDs
        file_records = defaultdict(str)
        for record in records:
            _id = get_patient_id(record)
            file_records[_id] += record

        # get the name of the annotations file corresponding to this record file
        file_version = "train" if not test else "test"
        file_id = "_".join(file_name.split(os.sep)[-1].split("_")[1:3])
        annot_file_name = "/".join(file_name.split("/")[:-2] + ["Annotations"] + ["annotations_" + file_id + "_" + file_version + ".json"])

        for _id in file_records.keys():
            record = Record(_id, file_records[_id], file_name, get_annotation(_id, annot_file_name))
            all_patients.append(record)

    # Array of all patient strings. May be multiple records for each patient
    return sorted(all_patients, key=lambda r: int(r.pid[3:]))

def split_records(file_name):
    file = open(file_name)
    text = file.read()
    text = "DUMMY " + text
    file.close()

    records = text.split("**PROTECTED[begin]")
    return records[1:] # The first record is "DUMMY " Don't return that one

# For testing
def print_patient_IDs(patients):
    for patient in patients:
        first_section = rx_tagged_section.search(patient.record)
        if not first_section:
            sys.stderr.write("Couldn't find patient ID\n")
            print(patient)
        else:
            print(first_section.group(2).strip("\n"))

def get_patients(dir):
    '''
    This is what to call from other programs.
    Takes a string of a directory path.
    Returns a list of record objects
    '''
    return get_records(get_file_list(dir))

def load_records(dir, test=False):
    return get_records(get_file_list(dir), test)

if __name__ == "__main__":
    files = get_file_list(sys.argv[1])
    # List of Patient strings. The method splits on the opening line,
    # so "**PROTECTED[begin]" is deleted. It'd be easy enough to add back in if necessary
    records = get_records(files, False)
    with open(sys.argv[2], "w") as out_file:
        print(records[0].record)
        for record in records:
            parse = record.parse()
            record.dump(out_file)
