'''
Breast and Lung Cancer Grading Pipeline

@authors: Eli Miller, Will Kearns

Contains the top-level code for classifying a patient's histological grade.
Makes calls to other more specific programs; manages and outputs what they return.
See documentation for more information.
'''
import sys
from patient_splitter import load_records
from patient import Patient

# USAGE: python3 main.py train_dir test_dir

train_dir = sys.argv[1]
test_dir = sys.argv[2]

# call patient_splitter to get a list of patient records
patients = [Patient(record) for record in load_records(train_dir)]
print(patients[0].record.text)
print(patients[0].record.sections)


"""
for patient in patients:
    # do whatever to classify the patient
    # python programs should preferably have a callable function which returns the data we need
    # non-python programs should print output to standard out and can be called from the command line with subprocess.check_output(["param1", "param2"], universal_newlines=True)
    # e.g. subprocess.check_output(["java", "MyProgram", "needed_directory"], universal_newlines=True)    

    # output classification to whatever format we're going to use
    print(patient.record.text)
"""