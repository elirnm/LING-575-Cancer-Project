import re

'''
Krista Watkins
Usage: call classify_record(record.text)

Rule-based classification
(In progress)
Returns integers 0-4
    0 for unknown (default)

Implemented:
    Find numerical grade to the right of "Histologic Grade"
To Implement:
    Find grade elsewhere in the document
'''

# Rexeges
num_str = "one|two|three|four|five|six|seven|eight|nine"
hist_title_rx = re.compile("histologic grade:", re.IGNORECASE)

'''
Groups
0: all
1: words preceding grade numbers
2: at least
3: nottingham
4: grade or g
5: whole number string
6: first number
7: 'of' or '/' second number
8: 'of' or '/'
9: second number
'''
number_grade_rx = re.compile("histologic grade:\\s*((at least)?\\s*(nottingham|bloom-richardson)?\\s*(grade|g|score)?)\\s*((\\d+|I+[XV]?|VI*|%s)\\s*((/|of)\\s*(\\d+|III|IV|IX|three|four|nine))?)"%num_str, re.IGNORECASE)
differentiation_rx = re.compile("histologic grade:\\s*((poorly|moderately|moderate|well)(\\s+(to|and)\\s+(poorly|moderately|moderate|well))?\\s+differentiated)", re.IGNORECASE)
word_grade_rx = re.compile("histologic grade:\\s*(low|intermediate|moderate|high)(\\s+(to|and)\\s+(low|intermediate|moderate|high))?(\\s+grade)?", re.IGNORECASE);
# Numbers are in groups 6 and 9
overall_grade_rx = re.compile("(overall\\s+grade|total\\s+score|nottingham\\s+histologic\\s+(grade|score|score-grade))\\s*(:)?\\s*(grade|g|score)?\\s*((\\d+|I+[XV]?|VI*|%s)+\\s*((/|of)\\s*(\\d+|III|IV|IX|three|four|nine))?)"%num_str, re.IGNORECASE)
form_grade_rx = re.compile("_*x_*\\s*grade\\s*(\\d+|I+V?|one|two|three|four)", re.IGNORECASE)

first_end_tag_rx = re.compile("Histologic grade:.*?</\\w+>", re.IGNORECASE|re.DOTALL)

'''
For testing: prints all the subgroups in a match
'''
def print_groups(match):
    print("Whole match: ", match.group())
    i = 0
    for group in match.groups():
        i += 1
        print(i, ":", group)

def classify_record(patient):
    gradeNumber = 0
    
    # There may be more than one record
    histology_headers = hist_title_rx.finditer(patient)

    grades = []
    start_indices = []
    section_count = 0
    header_count = 0

    # Find the locations of "Histology Grade:"
    for header_match in histology_headers:
        header_count += 1
        start_indices.append(header_match.start())

    section_count = len(start_indices)

    for i in range(0,section_count):
        stop_index = len(patient)
        if i < section_count - 1:
            stop_index = start_indices[i+1]
        section = patient[start_indices[i]:stop_index]

        # Find numerical grade numbers immidiately to the right of "Histology Grade:"
        number_found = number_grade_rx.search(section)
        if number_found:
            grades.append(extract_grade(number_found, 6, 9))

        # Search for other indicators in the same line
        else:
            differentiation_found = differentiation_rx.search(section)
            if differentiation_found:
                grades.append(extract_word_grade(differentiation_found, "diff"))

            else:
                word_grade_found = word_grade_rx.search(section)
                if word_grade_found:
                    grades.append(extract_word_grade(word_grade_found, "grade"))

                else:
                    # Look for the overall grade farther along in the section
                    # Only include text before the next end tag </something>
                    section = first_end_tag_rx.search(section).group()

                    overall_grade_found = overall_grade_rx.search(section)
                    if overall_grade_found:
                        grades.append(extract_grade(overall_grade_found, 6, 9))
                    else:
                        form_grade_found = form_grade_rx.search(section)
                        if form_grade_found:
                            grades.append(extract_grade(form_grade_found, 1, None))


    if len(grades) > 0:
        return grades

    # No histology headers were found
    if header_count == 0:
        return [0]

    return [0]

# Returns a grade number for matches of the form x (of y), and its variations
def extract_grade(match, first_num_location, second_num_location):
    num_1_str = match.group(first_num_location).lower()
    
    first_num = extract_number(num_1_str)
    
    # contains a maximum number (x of x)
    if second_num_location != None:
        num_2_str = match.group(second_num_location)
        if num_2_str != None:
            num_2_str = num_2_str.lower()
            second_num = extract_number(num_2_str)
            if second_num == 9:
                first_num = convert_from_nottingham(first_num)
    # only contains one number (grade x)
    else:
        if first_num > 3:
            first_num = convert_from_nottingham(first_num)

    return first_num

def extract_number(string):
    if string == '1' or string == "i" or string == "one":
        number = 1
    elif string == '2' or string == "ii" or string == "two":
        number = 2
    elif string == '3' or string == "iii" or string == "three":
        number = 3
    elif string == '4' or string == "iv" or string == "four":
        number = 4
    elif string == '5' or string == "v" or string == "five":
        number = 5
    elif string == '6' or string == "vi" or string == "six" :
        number = 6
    elif string == '7' or string == "vii" or string == "seven":
        number = 7
    elif string == '8' or string == "viii" or string == "eight":
        number = 8
    elif string == '9' or string == "ix" or string == "nine":
        number = 9
    else:
        number = 0

    return number

def convert_from_nottingham(nottingham_num):
    if nottingham_num < 6:
        return 1
    elif nottingham_num > 7:
        return 3
    else:
        return 2

'''
1: low/ well differentiated
2: intermediate/ moderately differentiated
3: high/ poorly differentiated
'''
def extract_word_grade(match, word_type):
    if word_type == "diff":
        groups = (2, 5)
    elif word_type == "grade":
        groups = (1, 4)
    
    grade_word = match.group(groups[0])

    # for "poor to moderately" or "moderately to well"
    alternate_word = match.group(groups[1])
    score = diff_to_num(grade_word)

    if alternate_word != None:
        alternate_score = diff_to_num(alternate_word)
        return max(score, alternate_score)

    else:
        return score

def diff_to_num(word):
    word = word.lower()
    if word == "poorly" or word == "poor" or word == "high":
        return 3
    if word == "moderately" or word == "moderate" or word == "intermediate":
        return 2
    if word == "well" or word == "low":
        return 1

'''
Testing
'''
if __name__ == "__main__":
    # Three lines so that local modules will be recognized
    # workaround for spyder.
    import sys
    import os
    sys.path.append(os.path.abspath("."))
    # For testing
    import patient_splitter
    import annotation_matcher
    import record
    
    
    records = patient_splitter.load_records("../data")
    errors = []
    # Misclassified in Annotations
    ignore = ['PAT7', 'PAT14', 'REC15', 'REC74', 'REC86', 'PAT157', 'REC720']
    for record_obj in records:
        gold_string = annotation_matcher.search_annotation(record_obj.annotation, "Grade Category")
        number_found = re.search("\d", gold_string)
        if number_found:
            gold = int(number_found.group())
        else:
            gold = 0
        grades = classify_record(record_obj.text)
        
        if gold not in grades and grades[0] != 0 and record_obj.rid not in ignore:
            print(record_obj.rid, grades, gold_string)
            
        if len(grades) > 1:
            print(record_obj.rid, grades, gold_string)
