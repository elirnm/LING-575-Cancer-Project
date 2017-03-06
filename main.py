import sys
import os
from random import randrange
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
report_errors = len(sys.argv) == 3
if report_errors:
    ea = open(sys.argv[2], 'w')

# call patient_splitter to get a list of patient records
train_records = patient_splitter.load_records(data_dir)
# leave the next line commented out until we're ready to run on test data
# test_records = patient_splitter.load_records(data_dir, test=True)

# train the ML classifier
# labels: 0 == no grade, 1 == has a grade
positive_lines = []
negative_lines = []
for record in train_records:
    grade_text = annotation_matcher.search_annotation(record.annotation, "Histologic Grade Text").split(";")
    for grade in grade_text:
        if grade == "":
            continue
        found = False
        for line in record.text.split("\n"):
            # add metamap stuff to the lines here before adding them to the positive/negative lists
            if grade in line and not found:
                positive_lines.append(line)
                found = True
            elif grade not in line:
                negative_lines.append(line)
# change this next line if we want more even numbers of positive and negative examples (we probably do)
culled_negatives = []
used = set()
while len(culled_negatives) <= len(positive_lines):
    r = randrange(0, len(negative_lines))
    if negative_lines[r] not in used:
        used.add(negative_lines[r])
        culled_negatives.append(negative_lines[r])
training_lines = [(x, "1") for x in positive_lines] + [(x, "0") for x in negative_lines]
count_vect, classifier = ml_classifier.train(training_lines)

# classify each record
# rb_* variables track results of rule-based classifier only
# ml_* variables track results of machine learning classifier only
# generic variables track results of system as a whole
# list variable are of form [count for records, count for tumors]
seen = 0
should_have_class = [0, 0]
classified, rb_classified, ml_classified = [0, 0], [0, 0], [0, 0]
correct, rb_correct, ml_correct = 0, 0, 0
rb_spec_correct, ml_spec_correct = 0, 0
rb_full_correct, ml_full_correct = 0, 0
# initialize variables for doing error analysis here
if report_errors:
    wrong_should_have_no_class = []
    wrong_should_have_class = []
    incorrect = []
    len_mismatches = []
for record in train_records:
    gold = record.gold
    rb_grade = rule_based_classifier.classify_record(record.text)
    ml_grade = ml_classifier.test(classifier, count_vect, record.text.split("\n"))
    ml_grade = [int(x) for x in ml_grade if x != "0"]
    seen += 1
    if gold != []:
        should_have_class[0] += 1
        should_have_class[1] += len(gold)
    if rb_grade != [0]:
        classified[0] += 1
        classified[1] += len(rb_grade)
        rb_classified[0] += 1
        rb_classified[1] += len(rb_grade)
    if ml_grade != []:
        ml_classified[0] += 1
        ml_classified[1] += len(ml_grade)
    if rb_grade == gold:
        rb_full_correct += 1
    if ml_grade == gold and ml_grade != []:
        ml_full_correct += 1
    for tumor_grade in rb_grade:
        if tumor_grade in gold:
            correct += 1
            rb_correct += 1
    for tumor_grade in ml_grade:
        if tumor_grade in gold:
            correct += 1
            ml_correct += 1
    for i in range(len(rb_grade)):
        if i >= len(gold):
            break
        if rb_grade[i] == gold[i]:
            rb_spec_correct += 1
    for i in range(len(ml_grade)):
        if i >= len(gold):
            break
        if ml_grade[i] == gold[i]:
            ml_spec_correct += 1

    # update variables for doing error analysis here
    if report_errors:
        pos_grades = [x for x in rb_grade if x != 0]
        rec_file = record.file.split(os.sep)[-1]
        if rb_grade != gold and gold != [] and grade != [0]:
            incorrect.append((rec_file + "/" + record.rid, rb_grade, gold))
        if rb_grade == [0] and gold != []:
            wrong_should_have_class.append((rec_file + "/" + record.rid, gold))
        if gold == [] and rb_grade != [0]:
            wrong_should_have_no_class.append((rec_file + "/" + record.rid, rb_grade))
        if len(pos_grades) != len(gold):
            len_mismatches.append((rec_file + "/" + record.rid, len(pos_grades), len(gold)))

# output accuracy data
print(str(seen) + " records processed")
print(str(should_have_class[1]) + " tumors in " + str(should_have_class[0]) + " records should be classified") 
# print(str(rb_classified[1]) + " tumors in " + str(rb_classified[0]) + " records classified -- rule-based")
# print(str(rb_correct) + " tumors correctly classified ignoring ordering (did the grade appear in the gold; it might not actually be correct for that tumor) -- rule-based")
# print(str(rb_full_correct) + " records classified fully correctly -- rule-based")
# print(str(rb_spec_correct) + " tumors classified with correct ordering (rough estimate) -- rule-based")
# print("Accuracy on records classified = " + str(correct / classified))
# print("Accuracy on records that should be classified = " + str(correct / should_have_class))
print(str(ml_classified[1]) + " tumors in " + str(ml_classified[0]) + " records classified -- machine learning")
print(str(ml_correct) + " tumors correctly classified ignoring ordering (did the grade appear in the gold; it might not actually be correct for that tumor) -- machine learning")
print(str(ml_full_correct) + " records classified fully correctly -- machine learning")
print(str(ml_spec_correct) + " tumors classified with correct ordering (rough estimate) -- machine learning")

# print information for doing error analysis here
if report_errors:
    ea.write(str(seen) + " records processed\n")
    ea.write(str(should_have_class[1]) + " tumors in " + str(should_have_class[0]) + " records should be classified\n") 
    ea.write(str(classified[1]) + " tumors in " + str(classified[0]) + " records classified\n")
    ea.write(str(correct) + " tumors correctly classified ignoring ordering (did the grade appear in the gold; it might not actually be correct for that tumor)\n")
    ea.write(str(full_correct) + " records classified fully correctly\n")
    ea.write(str(spec_correct) + " tumors classified with correct ordering (rough estimate)\n\n")
    # ea.write("Accuracy on records classified = " + str(correct / classified) + "\n")
    # ea.write("Accuracy on records that should be classified = " + str(correct / should_have_class) + "\n\n")

    ea.write("Records that should be unclassified but were given a class (" + str(len(wrong_should_have_no_class)) + "):\n")
    ea.write("Format: record, grade given\n")
    ea.write("\n".join([x[0] + ", " + str(x[1]) for x in wrong_should_have_no_class]) + "\n\n")

    ea.write("Records that were given the wrong class (" + str(len(incorrect)) + "):\n")
    ea.write("Format: record, given label, gold label\n")
    ea.write("\n".join(map(lambda x: x[0] + ", " + str(x[1]) + ", " + str(x[2]), incorrect)) + "\n\n")

    ea.write("Records that should be classified but were not given a class (" + str(len(wrong_should_have_class)) + "):\n")
    ea.write("Format: record, gold label\n")
    ea.write("\n".join([x[0] + ", " + str(x[1]) for x in wrong_should_have_class]) + "\n\n")

    ea.write("Records where length of the classified grade is different than the length of the gold standard (" + str(len(len_mismatches)) + "):\n")
    ea.write("Format: record, grade length, gold length\n")
    ea.write("\n".join([x[0] + ", " + str(x[1]) + ", " + str(x[2]) for x in len_mismatches]) + "\n")
