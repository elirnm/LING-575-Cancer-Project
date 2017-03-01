'''
Breast and Lung Cancer Grading Pipeline

@authors: Eli Miller, Will Kearns

Contains the top-level code for classifying a records's histological grade.
Makes calls to other more specific programs; manages and outputs what they return.
See documentation for more information.
'''
import sys
import os
import patient_splitter
import rule_based_classifier
import ml_classifier
import annotation_matcher

# USAGE: python3 main.py train_dir test_dir report_errors
# train_dir is the directory containing the training data files
# test_dir is the directory containing the test data files
# report_errors is optional. If it is present, error data will
#   be printed to a file with that name

train_dir = sys.argv[1]
test_dir = sys.argv[2]
report_errors = True if len(sys.argv) == 4 else False
if report_errors:
    ea = open(sys.argv[3], 'w')

# call patient_splitter to get a list of patient records
records = patient_splitter.load_records(train_dir)

# need to train the ML classifier here

# classify each record
seen = 0
should_have_class = 0
classified = 0
correct = 0
# add variables for doing error analysis here
if report_errors:
    wrong_should_have_no_class = []
    wrong_should_have_class = []
    incorrect = []
for record in records:
    gold = annotation_matcher.search_annotation(record.annotation, "Grade Category")
    grade = rule_based_classifier.classify_record(record.text)
    seen += 1
    if gold != "":
        should_have_class += 1
    if grade != 0:
        classified += 1
    if str(grade) in gold:
        correct += 1

    # update variables for doing error analysis here
    if report_errors:
        rec_file = record.file.split(os.sep)[-1]
        if str(grade) not in gold and gold != "" and grade != 0:
            incorrect.append((rec_file + "/" + record.rid, str(grade), gold))
        if grade == 0 and gold != "":
            wrong_should_have_class.append(rec_file + "/" + record.rid)
        if gold == "" and grade != 0:
            wrong_should_have_no_class.append(rec_file + "/" + record.rid)

# output accuracy data
print(str(seen) + " records processed")
print(str(should_have_class) + " records should be classified")
print(str(classified) + " records classified")
print(str(correct) + " records correctly classified")
print("Accuracy on records classified = " + str(correct / classified))
print("Accuracy on records that should be classified = " + str(correct / should_have_class))

# print information for doing error analysis here
if report_errors:
    ea.write(str(seen) + " records processed\n")
    ea.write(str(should_have_class) + " records should be classified\n")
    ea.write(str(classified) + " records classified\n")
    ea.write(str(correct) + " records correctly classified\n")
    ea.write("Accuracy on records classified = " + str(correct / classified) + "\n")
    ea.write("Accuracy on records that should be classified = " + str(correct / should_have_class) + "\n\n")

    ea.write("Records that should be unclassified but were given a class (" + str(len(wrong_should_have_no_class)) + "):\n")
    ea.write("\n".join(wrong_should_have_no_class) + "\n\n")

    ea.write("Records that were given the wrong class (" + str(len(incorrect)) + "):\n")
    ea.write("Format: record id, given label, gold label\n")
    ea.write("\n".join(map(lambda x: x[0] + ", " + str(x[1]) + ", " + str(x[2]), incorrect)) + "\n\n")

    ea.write("Records that should be classified but were not given a class (" + str(len(wrong_should_have_class)) + "):\n")
    ea.write("\n".join(wrong_should_have_class) + "\n")
