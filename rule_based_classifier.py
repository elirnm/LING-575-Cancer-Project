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
2: at least
3: nottingham
4: grade or g
5: whole number string
6: first number
7: 'of' or '/' second number
8: 'of' or '/'
9: second number
'''
number_grade_rx = re.compile("histologic grade:\\s*((at least)?\\s*(nottingham|bloom-richardson)?\\s*(grade|g|score)?)\\s*((\\d+|I|II|III|IV|V|VI|VII|VIII|IX|one|two|three|four|five|six|seven|eight|nine)+\\s*((/|of)\\s*(\\d+|III|IV|IX|three|four|nine))?)", re.IGNORECASE)
differentiation_rx = re.compile("histologic grade:\\s*((poorly|moderately|well)(\\s+(to|and)\\s+(poorly|moderately|well))?\\s+differentiated)", re.IGNORECASE)
word_grade_rx = re.compile("histologic grade:\\s*(low|intermediate|moderate|high)(\\s+(to|and)\\s+(low|intermediate|moderate|high))?(\\s+grade)?", re.IGNORECASE);
# Numbers are in groups 6 and 9
overall_grade_rx = re.compile("(overall\\s+grade|total\\s+score|nottingham\\s+histologic\\s+(grade|score|score-grade))\\s*(:)?\\s*(grade|g|score)?\\s*((\\d+|I|II|III|IV|V|VI|VII|VIII|IX|one|two|three|four|five|six|seven|eight|nine)+\\s*((/|of)\\s*(\\d+|III|IV|IX|three|four|nine))?)", re.IGNORECASE)
form_grade_rx = re.compile("_*x_*\\s*grade\\s*(\\d+|I|II|III|IV|one|two|three|four)", re.IGNORECASE)

first_end_tag_rx = re.compile("Histologic grade:.*?</\\w+>", re.IGNORECASE|re.DOTALL)


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
            grades.append(extract_number(number_found, 6, 9))

        # Search for other indicators in the same line
        else:
            differentiation_found = differentiation_rx.search(section)
            if differentiation_found:
                grades.append(extract_grade_from_diff(differentiation_found))

            else:
                word_grade_found = word_grade_rx.search(section)
                if word_grade_found:
                    grades.append(extract_grade_from_word(word_grade_found))

                else:
                    # Look for the overall grade farther along in the section
                    # Only include text before the next end tag </something>
                    section = first_end_tag_rx.search(section).group()

                    overall_grade_found = overall_grade_rx.search(section)
                    if overall_grade_found:
                        grades.append(extract_number(overall_grade_found, 6, 9))
                    else:
                        form_grade_found = form_grade_rx.search(section)
                        if form_grade_found:
                            grades.append(extract_number(form_grade_found, 1, None))


    if len(grades) > 1:
         # Where multiple grades differ, return the higher one
        return max(grades)

        # other option: return the most common grade
        # grade_stats = Counter(grades)
        #return grade_stats.most_common(1)[0][0]

    elif len(grades) == 1:
        return grades[0]

    # No histology headers were found
    if header_count == 0:
        return 0

    return gradeNumber

# Returns a grade number for matches of the form x (of y), and its variations
def extract_number(match, first_num_location, second_num_location):
    num_str_1 = match.group(first_num_location)
    if second_num_location != None:
        second_num_str = match.group(second_num_location)
    else:
        second_num_str = None

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

# grades for "poor/moderately/well" differentiated
def extract_grade_from_diff(match):
    grade_word = match.group(2)

    # for "poor to moderately" or "moderately to well"
    alternate_word = match.group(5)
    score = diff_to_num(grade_word)

    if alternate_word != None:
        alternate_score = diff_to_num(alternate_word)
        return max(score, alternate_score)

    else:
        return score

def extract_grade_from_word(match):
    grade_word = match.group(1)

    # for "poor to moderately" or "moderately to well"
    alternate_word = match.group(4)
    score = diff_to_num(grade_word)

    if alternate_word != None:
        alternate_score = diff_to_num(alternate_word)
        return max(score, alternate_score)

    else:
        return score

def diff_to_num(word):
    word = word.lower()
    if word == "poorly" or word == "high":
        return 3
    if word == "moderately" or (word == "moderate" or word == "intermediate"):
        return 2
    if word == "well" or word == "low":
        return 1

def convert_from_nottingham(nottingham_num):
    if nottingham_num < 6:
        return 1
    elif nottingham_num > 7:
        return 3
    else:
        return 2


