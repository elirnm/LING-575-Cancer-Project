import re
from collections import Counter
import sys

'''
Krista Watkins

Rule-based classification
(In progress)
Returns integer 0-4
    0 for unknown (default)

Implemented:
    Find numerical grade immediately to the right of "Histologic Grade"
To Implement:
    Find numerical grade farther along in the same line
    Find textual indications in the same line
    Find indicators elsewhere in the document
'''

# Rexeges
hist_title_rx = re.compile("histologic grade:", re.IGNORECASE)

'''
Groups
0: all
1: words preceding grade numbers
2: nottingham
3: grade or g
4: whole number string
5: first number
6: 'of' or '/' second number
7: 'of' or '/'
8: second number
'''
number_grade_rx = re.compile("histologic grade:\\s*((nottingham)?\\s*(grade|g)?)\\s*((\\d+|I|II|III|IV|V|VI|VII|VIII|IX)+\\s*((/|of)\\s*(\\d+|III|IX))?)", re.IGNORECASE)

def classify_record(patient):
    gradeNumber = 0
    
    # There may be more than one record
    histology_headers = hist_title_rx.finditer(patient)


    if not histology_headers == None:
        grades = []
        start_indices = []
        section_count = 0

        for header_match in histology_headers:
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
                grades.append(extract_number(number_found))

            # Search for other indicators in the same line
            else:
                x=1 #sys.stderr.write("add non-numerical histology line option\n")

        if len(grades) > 1:
            grade_stats = Counter(grades)
            sys.stderr.write("more than one grade")
            # Where multiple grades differ, return the most common
            return grade_stats.most_common(1)[0][0]

        elif len(grades) == 1:
            return grades[0]

    else:
        sys.stderr.write("Add no-histology-line option")


    return gradeNumber

def extract_number(match):
    num_str_1 = match.group(5)
    second_num_str = match.group(8)

    first_num = 0

    if num_str_1 == '1' or (num_str_1 == "I" or num_str_1 == "i"):
        first_num = 1
    elif num_str_1 == '2' or (num_str_1 == "II" or num_str_1 == "ii"):
        first_num = 2
    elif num_str_1 == '3' or (num_str_1 == "III" or num_str_1 == "iii"):
        first_num = 3
    elif num_str_1 == '4' or (num_str_1 == "IV" or num_str_1 == "iv"):
        first_num = 4
    elif num_str_1 == '5' or (num_str_1 == "V" or num_str_1 == "v"):
        first_num = 5
    elif num_str_1 == '6' or (num_str_1 == "VI" or num_str_1 == "vi"):
        first_num = 6
    elif num_str_1 == '7' or (num_str_1 == "VII" or num_str_1 == "vii"):
        first_num = 7
    elif num_str_1 == '8' or (num_str_1 == "VIII" or num_str_1 == "viii"):
        first_num = 8
    elif num_str_1 == '9' or (num_str_1 == "IX" or num_str_1 == "ix"):
        first_num = 9

    if second_num_str != None:
        if second_num_str == '9' or second_num_str == 'IX':
            return convert_from_nottingham(first_num)

    if first_num > 3:
        return convert_from_nottingham(first_num)

    return first_num

def convert_from_nottingham(nottingham_num):
    if nottingham_num < 6:
        return 1
    elif nottingham_num > 7:
        return 3
    else:
        return 2


