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
no-metamap is an optional string. If it is present, MetaMap Lite will
    not be used.
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
test_records = patient_splitter.load_records(data_dir, test=True)

# train the ML classifier
# labels: 0 == no grade, 1 == has a grade
positive_lines = []
negative_lines = []
for record in train_records:
    grade_text = annotation_matcher.search_annotation(record.annotation, "Histologic Grade Text").split("~")
    grades = []
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
        if grade not in line:
            negative_lines.append(line)
# randomly cull the negative examples so that we have a 50:50 positive/negative split of training data
culled_negatives = []
used = set()
while len(culled_negatives) < len(positive_lines):
    r = randrange(0, len(negative_lines))
    if negative_lines[r] not in used:
        selected_line = negative_lines[r]
        used.add(selected_line)
        if use_metamap:
            umls = record_module.get_UMLS_tags(selected_line)
            for term in umls:
                selected_line += " " + term.tag
                for concept in term.concepts:
                    selected_line += " " + concept.concept
        culled_negatives.append(selected_line)
training_lines = [(x, "1") for x in positive_lines] + [(x, "0") for x in culled_negatives]
trained_objects = ml_classifier.train(training_lines)

# classify each record
# rb_* variables track results of rule-based classifier only
# ml_* variables track results of machine learning classifier only
# generic and combo_* variables track results of system as a whole
seen = 0 # records processed
should_have_class = 0 # records that should have nonzero class
classified, rb_classified, ml_classified = 0, 0, 0 # records that were given nonzero class
correct, rb_correct, ml_correct = 0, 0, 0 # records given the correct grade, including correctly giving zero class
# accuracy matrices
combo_matrix = [[0 for _ in range(5)] for _ in range(5)]
rb_matrix = [[0 for _ in range(5)] for _ in range(5)]
ml_matrix = [[0 for _ in range(5)] for _ in range(5)]
# initialize variables for doing error analysis here
if report_errors:
    wrong_should_have_no_class = []
    wrong_should_have_class = []
    incorrect = []

def reset_variables():
    '''Resets all the results-tracking variables to initial state.'''
    global seen, combo_matrix, rb_matrix, ml_matrix, should_have_class
    global classified, rb_classified, ml_classified, correct, rb_correct, ml_correct
    global wrong_should_have_class, wrong_should_have_no_class, incorrect, len_mismatches
    seen = 0 # records processed
    should_have_class = 0 # records that should have nonzero class
    classified, rb_classified, ml_classified = 0, 0, 0 # records that were given nonzero class
    correct, rb_correct, ml_correct = 0, 0, 0 # records given the correct grade, including correctly giving zero class
    # accuracy matrices
    combo_matrix = [[0 for _ in range(5)] for _ in range(5)]
    rb_matrix = [[0 for _ in range(5)] for _ in range(5)]
    ml_matrix = [[0 for _ in range(5)] for _ in range(5)]
    # variables for doing error analysis
    if report_errors:
        wrong_should_have_no_class = []
        wrong_should_have_class = []
        incorrect = []

def classify(records_list):
    '''Classifies all the records in the given list of records.'''
    global seen, combo_matrix, rb_matrix, ml_matrix, should_have_class
    global classified, rb_classified, ml_classified, correct, rb_correct, ml_correct
    global wrong_should_have_class, wrong_should_have_no_class, incorrect
    for record in records_list:
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
        try:
            combo_matrix[best_grade][best_gold] += 1
            rb_matrix[rb_best_grade][best_gold] += 1
            ml_matrix[ml_best_grade][best_gold] += 1
        except IndexError as e:
            print("Bad annotation:", file=sys.stderr)
            print("File: " + record.file, file=sys.stderr)
            print("Record ID: " + str(record.rid), file=sys.stderr)
            print("Grade: " + str(best_gold), file=sys.stderr)
        if gold != []:
            should_have_class += 1

        # update variables for doing error analysis
        if report_errors:
            pos_grades = [x for x in rb_grade if x != 0]
            rec_file = record.file.split(os.sep)[-1]
            if best_grade != best_gold and best_gold != 0 and best_grade != 0:
                incorrect.append((rec_file + "/" + record.rid, best_grade, best_gold))
            if best_grade == 0 and best_gold != 0:
                wrong_should_have_class.append((rec_file + "/" + record.rid, best_gold))
            if best_gold == 0 and best_grade != 0:
                wrong_should_have_no_class.append((rec_file + "/" + record.rid, best_grade))

# output accuracy data
def print_results(matrix):
    binary_true_positive = matrix[1][1] + matrix[1][2] + matrix[1][3] + matrix[1][4] + matrix[2][1] + matrix[2][2] + matrix[2][3] + matrix[2][4]
    binary_true_positive += matrix[3][1] + matrix[3][2] + matrix[3][3] + matrix[3][4] + matrix[4][1] + matrix[4][2] + matrix[4][3] + matrix[4][4]
    binary_false_positive = matrix[1][0] + matrix[2][0] + matrix[3][0] + matrix[4][0]
    binary_true_negative = matrix[0][0]
    binary_false_negative = matrix[0][1] + matrix[0][2] + matrix[0][3] + matrix[0][4]

    print("Records processed: " + str(seen))
    print("Records which should not have a grade given:" + str(seen - should_have_class))
    print("Records which should have a grade given: "+ str(should_have_class))
    print("Records not given a grade: " + str(binary_true_negative + binary_false_negative))
    print("Records given a grade: " + str(binary_false_positive + binary_true_positive))
    print("Binary accuracy: " + str((binary_true_positive + binary_true_negative) / seen))
    binary_precision = binary_true_positive / (binary_true_positive + binary_false_positive)
    binary_recall = binary_true_positive / should_have_class
    print("Binary precision: " + str(binary_precision))
    print("Binary recall: " + str(binary_recall))
    print("Binary F1-Score: " + str(((binary_precision * binary_recall) / (binary_precision + binary_recall)) * 2))
    print("Binary specificity: " + str(binary_true_negative / (binary_true_negative + binary_false_positive)))
    try:
        print("Binary NPV: " + str(binary_true_negative / (binary_true_negative + binary_false_negative)))
    except ZeroDivisionError as e:
        print("Binary NPV: N/A (no records given negative classification)")
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
    print("Specific accuracy excluding negatives:" + str((matrix[1][1] + matrix[2][2] + matrix[3][3] + matrix[4][4]) / should_have_class))
    print("Specific accuracy over records that we gave a grade: " + str((matrix[1][1] + matrix[2][2] + matrix[3][3] + matrix[4][4]) / (binary_true_positive + binary_false_positive)))

def write_errors():
    '''Writes data for doing error analysis.'''
    ea.write("Records processed: " + str(seen) + "\n\n")
    
    ea.write("Records that should be unclassified but were given a class: " + str(len(wrong_should_have_no_class)) + "\n")
    ea.write("Format: record, grade given\n")
    ea.write("\n".join([x[0] + ", " + str(x[1]) for x in wrong_should_have_no_class]) + "\n\n")

    ea.write("Records that were given the wrong class: " + str(len(incorrect)) + "\n")
    ea.write("Format: record, given label, gold label\n")
    ea.write("\n".join(map(lambda x: x[0] + ", " + str(x[1]) + ", " + str(x[2]), incorrect)) + "\n\n")

    ea.write("Records that should be classified but were not given a class: " + str(len(wrong_should_have_class)) + "\n")
    ea.write("Format: record, gold label\n")
    ea.write("\n".join([x[0] + ", " + str(x[1]) for x in wrong_should_have_class]) + "\n\n")

# test on training data
classify(train_records)

# print training results
print("Results on training data")
print("-------------------------------------------------")
# print combined results
print("Combined")
print("---------")
print_results(combo_matrix)
if report_errors:
    ea.write("Training data errors\n")
    ea.write("-------------------------------------------------\n")
    ea.write("Combined\n")
    ea.write("---------\n")
    write_errors()

if full_results:
    # print rule-based results
    print()
    print()
    print("Rule-based Only")
    print("----------------")
    print_results(rb_matrix)
    if report_errors:
        ea.write("Rule-based only\n")
        ea.write("----------------\n")
        write_errors()

    # print machine learning results
    print()
    print()
    print("Machine Learning Only")
    print("----------------------")
    print_results(ml_matrix)
    if report_errors:
        ea.write("Machine Learning only\n")
        ea.write("----------------------\n")
        write_errors()

# test on test data
reset_variables()
classify(test_records)

# print test results
print()
print()
print("Results on test data")
print("-------------------------------------------------")
# print combined results
print("Combined")
print("---------")
print_results(combo_matrix)
if report_errors:
    ea.write("Test data errors\n")
    ea.write("-------------------------------------------------\n")
    ea.write("Combined\n")
    ea.write("---------\n")
    write_errors()

if full_results:
    # print rule-based results
    print()
    print()
    print("Rule-based Only")
    print("----------------")
    print_results(rb_matrix)
    if report_errors:
        ea.write("Rule-based only\n")
        ea.write("----------------\n")
        write_errors()

    # print machine learning results
    print()
    print()
    print("Machine Learning Only")
    print("----------------------")
    print_results(ml_matrix)
    if report_errors:
        ea.write("Machine Learning only\n")
        ea.write("----------------------\n")
        write_errors()
