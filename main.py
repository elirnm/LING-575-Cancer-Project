import sys
import os
import patient_splitter
import rule_based_classifier
import ml_classifier
import annotation_matcher

'''
Breast and Lung Cancer Grading Pipeline

@authors: Eli Miller, Will Kearns

Contains the top-level code for classifying a records's histological grade.
Makes calls to other more specific programs; manages and outputs what they return.


USAGE: python(3) main.py data_dir error_file

data_dir is the directory containing the data files.
error_file is optional. If it is present, error data will
    be printed to a file with that name.
'''

data_dir = sys.argv[1]
report_errors = True if len(sys.argv) == 3 else False
if report_errors:
    ea = open(sys.argv[2], 'w')

# call patient_splitter to get a list of patient records
train_records = patient_splitter.load_records(data_dir)
# leave the next line commented out until we're ready to run on test data
# test_records = patient_splitter.load_records(data_dir, test=True)

# need to train the ML classifier here

# classify each record
# rb_* variables track results of rule-based classifier only
# ml_* variables track results of machine learning classifier only
# generic variables track results of system as a whole
# list variable are of form [count for records, count for tumors]
seen = 0
should_have_class = [0, 0]
classified, rb_classified, ml_classified = [0, 0], [0, 0], [0, 0]
correct, rb_correct, ml_correct = 0, 0, 0
spec_correct = 0
full_correct = 0
# initialize variables for doing error analysis here
if report_errors:
    wrong_should_have_no_class = []
    wrong_should_have_class = []
    incorrect = []
    len_mismatches = []
for record in train_records:
    gold = record.gold
    grade = rule_based_classifier.classify_record(record.text)
    seen += 1
    if gold != []:
        should_have_class[0] += 1
        should_have_class[1] += len(gold)
    if grade != [0]:
        classified[0] += 1
        classified[1] += len(grade)
        rb_classified[0] += 1
        rb_classified[1] += len(grade)
    if grade == gold:
        full_correct += 1
    for tumor_grade in grade:
        if tumor_grade in gold:
            correct += 1
            rb_correct += 1
    for i in range(len(grade)):
        if i >= len(gold):
            break
        if grade[i] == gold[i]:
            spec_correct += 1

    # update variables for doing error analysis here
    if report_errors:
        rec_file = record.file.split(os.sep)[-1]
        if len([x for x in grade if x != 0]) != len(gold):
            len_mismatches.append((rec_file, len([x for x in grade if x != 0]), len(gold)))
        # if str(grade) not in gold and gold != "" and grade != 0:
        #     incorrect.append((rec_file + "/" + record.rid, str(grade), gold))
        # if grade == 0 and gold != "":
        #     wrong_should_have_class.append(rec_file + "/" + record.rid)
        # if gold == "" and grade != 0:
        #     wrong_should_have_no_class.append(rec_file + "/" + record.rid)

# output accuracy data
print(str(seen) + " records processed")
print(str(should_have_class[0]) + " records should be classified, " + str(should_have_class[1]) + " tumors should be classified") 
print(str(classified[0]) + " records classified, " + str(classified[1]) + " tumors classified")
print(str(correct) + " tumors correctly classified ignoring ordering (did the grade appear in the gold; it might not actually be correct for that tumor)")
print(str(full_correct) + " records classified fully correctly")
print(str(spec_correct) + " tumors classified with correct ordering (rough estimate)")
# print("Accuracy on records classified = " + str(correct / classified))
# print("Accuracy on records that should be classified = " + str(correct / should_have_class))

# print information for doing error analysis here
if report_errors:
    # ea.write(str(seen) + " records processed\n")
    # ea.write(str(should_have_class) + " records should be classified\n")
    # ea.write(str(classified) + " records classified\n")
    # ea.write(str(correct) + " records correctly classified\n")
    # ea.write("Accuracy on records classified = " + str(correct / classified) + "\n")
    # ea.write("Accuracy on records that should be classified = " + str(correct / should_have_class) + "\n\n")

    # ea.write("Records that should be unclassified but were given a class (" + str(len(wrong_should_have_no_class)) + "):\n")
    # ea.write("\n".join(wrong_should_have_no_class) + "\n\n")

    # ea.write("Records that were given the wrong class (" + str(len(incorrect)) + "):\n")
    # ea.write("Format: record id, given label, gold label\n")
    # ea.write("\n".join(map(lambda x: x[0] + ", " + str(x[1]) + ", " + x[2], incorrect)) + "\n\n")

    # ea.write("Records that should be classified but were not given a class (" + str(len(wrong_should_have_class)) + "):\n")
    # ea.write("\n".join(wrong_should_have_class) + "\n")

    ea.write("Records where length of the classified grade is different than the length of the gold standard (" + str(len(len_mismatches)) + ")\n")
    ea.write("Format: file, grade length, gold length\n")
    ea.write("\n".join([x[0] + ", " + str(x[1]) + ", " + str(x[2]) for x in len_mismatches]) + "\n")
