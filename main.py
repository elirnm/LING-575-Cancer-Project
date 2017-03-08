import sys
import os
from random import randrange
import patient_splitter
import rule_based_classifier
import ml_classifier
import annotation_matcher
import record as record_module

'''
Breast and Lung Cancer Grading Pipeline

@authors: Eli Miller, Will Kearns

Contains the top-level code for classifying a records's histological grade.
Makes calls to other more specific programs; manages and outputs what they return.


USAGE: python(3) main.py data_dir print-errors no-metamap full-results

data_dir is the directory containing the data files.
print-errors is an optional string. If it is present, error data will
    be printed to an "error_analysis.txt" file.
no-metamap is an optional string. If it is present, metamap will not
    be used.
full-results is an optional string. If it is present, the program will
    print results for each module as well as combined results.
'''
# Corrections for incorrectly-annotated records
corrections = {'PAT7':[1], 'PAT14':[2], 'REC86':[1], 'PAT157':[1], 'REC720':[3], 'REC191':[1], 'REC798':[3]}

data_dir = sys.argv[1]
report_errors = "print-errors" in sys.argv
if report_errors:
    ea = open("error_analysis.txt", 'w')
use_metamap = "no-metamap" not in sys.argv
if use_metamap:
    from config import METAMAP_DIR
    if not os.path.exists(METAMAP_DIR):
        print("MetaMap Lite installation not found. To use MetaMap Lite, install it and edit config.py. Running without MetaMap Lite.", file=sys.stderr)
        use_metamap = False
full_results = "full-results" in sys.argv

# call patient_splitter to get a list of patient records
train_records = patient_splitter.load_records(data_dir)
# leave the next line commented out until we're ready to run on test data
# test_records = patient_splitter.load_records(data_dir, test=True)

# train the ML classifier
# labels: 0 == no grade, 1 == has a grade
positive_lines = []
negative_lines = []
for record in train_records:
    grade_text = annotation_matcher.search_annotation(record.annotation, "Histologic Grade Text").split("~")
    # if len(grade_text) > len(annotation_matcher.search_annotation(record.annotation, "Grade Category").split("~")):
    #     print(record.file + "/" + str(record.rid))
    for grade in grade_text:
        if grade == "":
            continue
        # for line in record.text.split("\n"):
            # # add metamap stuff to the lines here before adding them to the positive/negative lists
            # if grade in line:
            #     positive_lines.append(line)
            # else:
            #     negative_lines.append(line)
        if use_metamap:
            umls = record_module.get_UMLS_tags(grade)
            for term in umls:
                grade += " " + term.tag
                for concept in term.concepts:
                    grade += " " + concept.concept
        positive_lines.append(grade) # add metamap stuff here
    for line in record.text.split("\n"):
        if use_metamap:
            umls = record_module.get_UMLS_tags(line)
            for term in umls:
                line += " " + term.tag
                for concept in term.concepts:
                    line += " " + concept.concept
        if grade not in line:
            negative_lines.append(line)
# randomly cull the negative examples so that we have a 50:50 positive/negative split of training data
culled_negatives = []
used = set()
while len(culled_negatives) < len(positive_lines):
    r = randrange(0, len(negative_lines))
    if negative_lines[r] not in used:
        used.add(negative_lines[r])
        culled_negatives.append(negative_lines[r])
training_lines = [(x, "1") for x in positive_lines] + [(x, "0") for x in culled_negatives]
trained_objects = ml_classifier.train(training_lines)

# classify each record
# rb_* variables track results of rule-based classifier only
# ml_* variables track results of machine learning classifier only
# generic variables track results of system as a whole
matrix = [[0 for _ in range(5)] for _ in range(5)]
rb_matrix = [[0 for _ in range(5)] for _ in range(5)]
ml_matrix = [[0 for _ in range(5)] for _ in range(5)]
seen = 0 # records processed
should_have_class = [0, 0] # records that should have nonzero class
classified, rb_classified, ml_classified = 0, 0, 0 # records that were given nonzero class
correct, rb_correct, ml_correct = 0, 0, 0 # records given correct grade -- including correctly giving zero class
positive_correct, rb_positive_correct, ml_positive_correct = 0, 0, 0 # records given correct grade -- excluding nonzero class
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
    rb_grade = rule_based_classifier.classify_record(record.text, 2)
        # Options for dealing with "differentiation" strings
        # 0: Skip differentiation search
        # 1: Return max diff, if there's more than one
        # 2: skip "poorly differentiated"
    ml_lines = record.text.split("\n")
    ml_grade = ml_classifier.test(trained_objects, ml_lines)
    for i in range(len(ml_grade) - 1, -1, -1):
        if ml_grade[i] == "0":
            del ml_lines[i]
    ml_grade = [int(x) for x in ml_grade if x != "0"]
    # extract the specific grade from the lines
    ml_grade = [rule_based_classifier.classify_string(x) for x in ml_lines]
    # get best combined grade
    combo_grades = rb_grade + ml_grade
    counts = {0:0, 1:0, 2:0, 3:0, 4:0}
    rb_counts = {0:0, 1:0, 2:0, 3:0, 4:0}
    ml_counts = {0:0, 1:0, 2:0, 3:0, 4:0}
    for grade in combo_grades:
        counts[grade] += 1
    for grade in rb_grade:
        rb_counts[grade] += 1
    for grade in ml_grade:
        ml_counts[grade] += 1
    counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    rb_counts = sorted(rb_counts.items(), key=lambda x: x[1], reverse=True)
    ml_counts = sorted(ml_counts.items(), key=lambda x: x[1], reverse=True)
    if counts == []:
        best_grade = 0
    else:
        if counts[0][1] == counts[1][1]:
            best_grade = max(counts[0][0], counts[1][0])
        else:
            best_grade = counts[0][0]
    if rb_counts == []:
        rb_best_grade = 0
    else:
        if rb_counts[0][1] == rb_counts[1][1]:
            rb_best_grade = max(rb_counts[0][0], rb_counts[1][0])
        else:
            rb_best_grade = rb_counts[0][0]
    if ml_counts == []:
        ml_best_grade = 0
    else:
        if ml_counts[0][1] == ml_counts[1][1]:
            ml_best_grade = max(ml_counts[0][0], ml_counts[1][0])
        else:
            ml_best_grade = ml_counts[0][0]
    best_gold = max(gold) if gold != [] else 0
    # count for accuracy
    seen += 1
    matrix[best_grade][best_gold] += 1
    rb_matrix[rb_best_grade][best_gold] += 1
    ml_matrix[ml_best_grade][best_gold] += 1
    if gold != []:
        should_have_class[0] += 1
        should_have_class[1] += len(gold)

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
# print combined results
binary_true_positive = matrix[1][1] + matrix[1][2] + matrix[1][3] + matrix[1][4] + matrix[2][1] + matrix[2][2] + matrix[2][3] + matrix[2][4]
binary_true_positive += matrix[3][1] + matrix[3][2] + matrix[3][3] + matrix[3][4] + matrix[4][1] + matrix[4][2] + matrix[4][3] + matrix[4][4]
binary_false_positive = matrix[1][0] + matrix[2][0] + matrix[3][0] + matrix[4][0]
binary_true_negative = matrix[0][0]
binary_false_negative = matrix[0][1] + matrix[0][2] + matrix[0][3] + matrix[0][4]

print("Combined")
print("---------")
print("Records processed: " + str(seen))
print("Records which should not have a grade given:" + str(seen - should_have_class[0]))
print("Records which should have a grade given: "+ str(should_have_class[0]))
print("Records not given a grade: " + str(binary_true_negative + binary_false_negative))
print("Records given a grade: " + str(binary_false_positive + binary_true_positive))
print("Binary accuracy: " + str((binary_true_positive + binary_true_negative) / seen))
binary_precision = binary_true_positive / (binary_true_positive + binary_false_positive)
binary_recall = binary_true_positive / should_have_class[0]
print("Binary precision: " + str(binary_precision))
print("Binary recall: " + str(binary_recall))
print("Binary F1-Score: " + str(((binary_precision * binary_recall) / (binary_precision + binary_recall)) * 2))
print("Binary specificity: " + str(binary_true_negative / (binary_true_negative + binary_false_positive)))
print("Binary NPV: " + str(binary_true_negative / (binary_true_negative + binary_false_negative)))
print()
print("Confusion matrix")
print("Assigned grade on the left, gold grade along the top")
print("0 = no grade")
print()
print("  | 0\t1\t2\t3\t4")
print("--+-----------------------------------")
for i in range(len(matrix)):
    print(str(i) + " | ", end='')
    for j in range(len(matrix[i])):
        print(str(matrix[i][j]) + "\t", end='')
    print()
print()
print("Specific accuracy:" + str((matrix[0][0] + matrix[1][1] + matrix[2][2] + matrix[3][3] + matrix[4][4]) / seen))
print("Specific accuracy excluding negatives:" + str((matrix[1][1] + matrix[2][2] + matrix[3][3] + matrix[4][4]) / should_have_class[0]))

if full_results:
    # print rule-based results
    binary_true_positive = rb_matrix[1][1] + rb_matrix[1][2] + rb_matrix[1][3] + rb_matrix[1][4] + rb_matrix[2][1] + rb_matrix[2][2] + rb_matrix[2][3] + rb_matrix[2][4]
    binary_true_positive += rb_matrix[3][1] + rb_matrix[3][2] + rb_matrix[3][3] + rb_matrix[3][4] + rb_matrix[4][1] + rb_matrix[4][2] + rb_matrix[4][3] + rb_matrix[4][4]
    binary_false_positive = rb_matrix[1][0] + rb_matrix[2][0] + rb_matrix[3][0] + rb_matrix[4][0]
    binary_true_negative = rb_matrix[0][0]
    binary_false_negative = rb_matrix[0][1] + rb_matrix[0][2] + rb_matrix[0][3] + rb_matrix[0][4]

    print()
    print()
    print("Rule-based Only")
    print("----------------")
    print("Records processed: " + str(seen))
    print("Records which should not have a grade given:" + str(seen - should_have_class[0]))
    print("Records which should have a grade given: "+ str(should_have_class[0]))
    print("Records not given a grade: " + str(binary_true_negative + binary_false_negative))
    print("Records given a grade: " + str(binary_false_positive + binary_true_positive))
    print("Binary accuracy: " + str((binary_true_positive + binary_true_negative) / seen))
    binary_precision = binary_true_positive / (binary_true_positive + binary_false_positive)
    binary_recall = binary_true_positive / should_have_class[0]
    print("Binary precision: " + str(binary_precision))
    print("Binary recall: " + str(binary_recall))
    print("Binary F1-Score: " + str(((binary_precision * binary_recall) / (binary_precision + binary_recall)) * 2))
    print("Binary specificity: " + str(binary_true_negative / (binary_true_negative + binary_false_positive)))
    try:
        print("Binary NPV: " + str(binary_true_negative / (binary_true_negative + binary_false_negative)))
    except ZeroDivisionError as e:
        print("Binary NPV: N/A (division by zero): " + str(binary_true_negative) + " / " + str(binary_true_negative + binary_false_negative))
    print()
    print("Confusion matrix")
    print("Assigned grade on the left, gold grade along the top")
    print("0 = no grade")
    print()
    print("  | 0\t1\t2\t3\t4")
    print("--+-----------------------------------")
    for i in range(len(rb_matrix)):
        print(str(i) + " | ", end='')
        for j in range(len(rb_matrix[i])):
            print(str(rb_matrix[i][j]) + "\t", end='')
        print()
    print()
    print("Specific accuracy:" + str((rb_matrix[0][0] + rb_matrix[1][1] + rb_matrix[2][2] + rb_matrix[3][3] + rb_matrix[4][4]) / seen))
    print("Specific accuracy excluding negatives:" + str((rb_matrix[1][1] + rb_matrix[2][2] + rb_matrix[3][3] + rb_matrix[4][4]) / should_have_class[0]))

    # print machine learning results
    binary_true_positive = ml_matrix[1][1] + ml_matrix[1][2] + ml_matrix[1][3] + ml_matrix[1][4] + ml_matrix[2][1] + ml_matrix[2][2] + ml_matrix[2][3] + ml_matrix[2][4]
    binary_true_positive += ml_matrix[3][1] + ml_matrix[3][2] + ml_matrix[3][3] + ml_matrix[3][4] + ml_matrix[4][1] + ml_matrix[4][2] + ml_matrix[4][3] + ml_matrix[4][4]
    binary_false_positive = ml_matrix[1][0] + ml_matrix[2][0] + ml_matrix[3][0] + ml_matrix[4][0]
    binary_true_negative = ml_matrix[0][0]
    binary_false_negative = ml_matrix[0][1] + ml_matrix[0][2] + ml_matrix[0][3] + ml_matrix[0][4]

    print()
    print()
    print("Machine Learning Only")
    print("----------------------")
    print("Records processed: " + str(seen))
    print("Records which should not have a grade given:" + str(seen - should_have_class[0]))
    print("Records which should have a grade given: "+ str(should_have_class[0]))
    print("Records not given a grade: " + str(binary_true_negative + binary_false_negative))
    print("Records given a grade: " + str(binary_false_positive + binary_true_positive))
    print("Binary accuracy: " + str((binary_true_positive + binary_true_negative) / seen))
    binary_precision = binary_true_positive / (binary_true_positive + binary_false_positive)
    binary_recall = binary_true_positive / should_have_class[0]
    print("Binary precision: " + str(binary_precision))
    print("Binary recall: " + str(binary_recall))
    print("Binary F1-Score: " + str(((binary_precision * binary_recall) / (binary_precision + binary_recall)) * 2))
    print("Binary specificity: " + str(binary_true_negative / (binary_true_negative + binary_false_positive)))
    try:
        print("Binary NPV: " + str(binary_true_negative / (binary_true_negative + binary_false_negative)))
    except ZeroDivisionError as e:
        print("Binary NPV: N/A (division by zero): " + str(binary_true_negative) + " / " + str(binary_true_negative + binary_false_negative))
    print()
    print("Confusion matrix")
    print("Assigned grade on the left, gold grade along the top")
    print("0 = no grade")
    print()
    print("  | 0\t1\t2\t3\t4")
    print("--+-----------------------------------")
    for i in range(len(ml_matrix)):
        print(str(i) + " | ", end='')
        for j in range(len(ml_matrix[i])):
            print(str(ml_matrix[i][j]) + "\t", end='')
        print()
    print()
    print("Specific accuracy:" + str((ml_matrix[0][0] + ml_matrix[1][1] + ml_matrix[2][2] + ml_matrix[3][3] + ml_matrix[4][4]) / seen))
    print("Specific accuracy excluding negatives:" + str((ml_matrix[1][1] + ml_matrix[2][2] + ml_matrix[3][3] + ml_matrix[4][4]) / should_have_class[0]))

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
