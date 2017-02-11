import os
import sys
import re
from collections import defaultdict
from record import Record

'''
Patient Splitter Method
Krista Watkins
Feb 10

Usage: python3 recordSplitter.py directory_name

This doesn't promise a particular order for the patients. Is there any reason we'd care?
'''
rx_tagged_section = re.compile("<(\\w+)>(.+?)</\\1>", re.DOTALL)

def get_file_list(directory):
    dir_list = os.listdir(directory)
    file_list = []
    for item in dir_list:
        if item.endswith(".txt"):
            file_list.append(directory + "/" + item)
    return file_list

def get_patient_id(record):
    first_section = rx_tagged_section.search(record)
    if not first_section or first_section.group(1) != "PATIENT_DISPLAY_ID":
        sys.stderr.write("No Patient ID found:\n")
        sys.stderr.write(record)
        return "none"
    else:
        return first_section.group(2).strip("\n")

def get_patients(file_list):
    all_patients = []

    for file_name in file_list:
        records = split_records(file_name)

        # check for records with matching patient IDs
        file_records = defaultdict(str)
        for record in records:
            _id = get_patient_id(record)
            file_records[_id] += record

        for _id in file_records.keys():
            record = Record(_id, file_records[_id])
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


if __name__ == "__main__":
    files = get_file_list(sys.argv[1])
    # List of Patient strings. The method splits on the opening line,
    # so "**PROTECTED[begin]" is deleted. It'd be easy enough to add back in if necessary
    patients = get_patients(files)

    print_patient_IDs(patients)
