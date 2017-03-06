import re

# For test method search_phrase
from record import Record
from annotation_matcher import search_annotation # In check headers

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
histologic_grade_rx = re.compile("histologic\\s+(grade):?", re.IGNORECASE)
nottgham_hist_score_rx = re.compile("nottingham\\s+histologic\\s+score:?", re.IGNORECASE)
# Numbers in groups 4 and 7
number_grade_rx = re.compile("^(at\\s*least\\s*)?(grade|g)?\\s*((\\d+|I+[XV]?|VI*|%s)\\s*((/|of|out of)\\s*(\\d+|III|IV|IX|three|four|nine))?)"%num_str, re.IGNORECASE)
# Differentiation in groups 1 and 4. Starts at line beginning
differentiation_rx = re.compile("^(poorly|moderately|moderate|well)(\\s+(to|and)\\s+(poorly|moderately|moderate|well))?(\\s+|-)differentiated", re.IGNORECASE)
diff_anywhere_rx = re.compile("(poorly|moderately|moderate|well)(\\s+(to|and)\\s+(poorly|moderately|moderate|well))?(\\s+|-)differentiated", re.IGNORECASE)
# Words in groups 1 and 4
word_grade_rx = re.compile("^(low|intermediate|moderate|high)(\\s+(to|and)\\s+(low|intermediate|moderate|high))?", re.IGNORECASE);
# Numbers are in groups 6 and 9
overall_grade_rx = re.compile("(overall\\s+grade|total\\s+score|nottingham\\s+histologic\\s+(grade|score|score-grade))\\s*-?\\s*(:)?\\s*(grade|g|score)?\\s*-?\\s*((\\d+|I+[XV]?|VI*|%s)+\\s*((/|of)\\s*(\\d+|III|IV|IX|three|four|nine))?)"%num_str, re.IGNORECASE)
form_grade_rx = re.compile("_*x_*\\s*grade\\s*(\\d+|I+V?|one|two|three|four)", re.IGNORECASE)


'''
For testing: prints all the subgroups in a match
'''
def print_groups(match):
    print("Whole match: ", match.group())
    i = 0
    for group in match.groups():
        i += 1
        print(i, ":", group)

'''
For testing: prints 
'''    
def search_phrase(all_records, phrase):
    tagged = 0
    header_count = 0
    header_without_tag = 0
    tag_without_header = 0
    header_rx = re.compile(phrase, re.IGNORECASE)
    
    remaining = []
    
    for rec in all_records:
        header_found = header_rx.search(rec.text)
        has_grade = search_annotation(rec.annotation, "Grade Category") != ""
        
        if has_grade:
            print(search_annotation(rec.annotation, "Histologic Grade Text"))
            tagged += 1
            if not header_found:
                tag_without_header += 1
                remaining.append(rec)
            else:
                header_count += 1
        
        else:
            if header_found:
                header_without_tag += 1
                header_count += 1
    print("All with annontated grade:", tagged)
    print("Records with phrase:", phrase, header_count)
    print("Phrase and no grade", header_without_tag)
    print("Grade and no phrase", phrase, tag_without_header)
    return remaining

def classify_record(rec):
    # Try multiple header variations
    
    # Histologic Grade: (Nottingham histologic score)
    # Histologic Grade: Nottingham:
    grades = header_trial(rec, "histologic\\s+grade\\s*:?\\s*\(?nottingham\\s*(histologic)?\\s*(grade|score)?\)?\\s*:?\\s*")
    if len(grades) > 0:
        return grades
    
    # Histologic Grade: Bloom-richardson score
    grades = header_trial(rec, "histologic\\s+grade\\s*:\\s*bloom-richardson\\s+score\\s*")
    if len(grades) > 0:
        return grades
    
    # Histologic Grade:
    grades = header_trial(rec, "histologic\\s+grade\\s*:\\s*")
    if len(grades) > 0:
        return grades
    
    # Histologic Grade (MBR):
    # Histologic Grade (if applicable):
    grades = header_trial(rec, "histologic\\s+grade\\s*\((MBR|if\\s+applicable)\)\\s*:?\\s*")
    if len(grades) > 0:
        return grades
    
    # Histologic grade
    grades = header_trial(rec, "histologic\\s+grade\\s*")
    if len(grades) > 0:
        return grades
    
    # No headers found. Search for differentiation strings
    grades = diff_trial(rec)
    if len(grades) > 0:
        return grades
    else:
        return [0]

def header_trial(rec, regex):
    # Find sections with the given header
    histology_headers = re.finditer(regex, rec, re.IGNORECASE)
    starts = []
    ends = []
    # Headers may match regex but not be identical. Store variations
    headers = []
    count = 0
    for header_match in histology_headers:
        count += 1
        starts.append(header_match.start())
        headers.append(header_match.group())
        if count > 1:
            ends.append(header_match.start())
    if count > 0:
        ends.append(len(rec))
    
    # Attempt to find one grade per section
    grades = []
    for i in range(0, len(starts)):
        section = rec[starts[i] + len(headers[i]):ends[i]]
        grade = classify_section(section)
        if grade > 0:
            grades.append(grade)
            
    if len(grades) > 0:
        return grades
    elif count > 0:
        return[0]
    else:
        return []
    
def diff_trial(rec):
    diff_matches = diff_anywhere_rx.finditer(rec)
    grades = []
    
    for match in diff_matches:
        grade = extract_word_grade(match)
        grades.append(grade)
    return grades

def classify_section(section):
    # Find numerical grade at the beginning of the section
    number_found = number_grade_rx.search(section)
    if number_found:
        return extract_number_grade(number_found, 4, 7)

    # Find differentiation at the beginning of the section
    differentiation_found = differentiation_rx.search(section)
    if differentiation_found:
        return extract_word_grade(differentiation_found)
    
    # Low/medium/high grade at section beginning
    word_grade_found = word_grade_rx.search(section)
    if word_grade_found:
        return extract_word_grade(word_grade_found)


    # Look for the overall grade farther along in the section
    overall_grade_found = overall_grade_rx.search(section)
    if overall_grade_found:
        return extract_number_grade(overall_grade_found, 6, 9)

    # Look for grade in form format: Overall Grade: __x__
    form_grade_found = form_grade_rx.search(section)
    if form_grade_found:
        return extract_number_grade(form_grade_found, 1, None)

    return 0

'''
Methods for determining integer grade from a regex match or string
'''

# Returns a grade number for matches of the form x (of y), and its variations
def extract_number_grade(match, first_num_location, second_num_location):
    num_1_str = match.group(first_num_location).lower()
    
    first_num = parse_number(num_1_str)
    
    # contains a maximum number (x of x)
    if second_num_location != None:
        num_2_str = match.group(second_num_location)
        if num_2_str != None:
            num_2_str = num_2_str.lower()
            second_num = parse_number(num_2_str)
            if second_num == 9:
                first_num = convert_from_nottingham(first_num)
        elif first_num > 3:
            first_num = convert_from_nottingham(first_num)
    # only contains one number (grade x)
    else:
        if first_num > 3:
            first_num = convert_from_nottingham(first_num)

    return first_num

def parse_number(string):
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

def extract_word_grade(match):
    '''
    1: low/ well differentiated
    2: intermediate/ moderately differentiated
    3: high/ poorly differentiated
    '''

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
    # workaround for my spyder.
    import sys
    import os
    sys.path.append(os.path.abspath("."))
    # For testing
    import patient_splitter
    
    records = patient_splitter.load_records("../data/Reports")
    g_count = 0
    unclassified = []
    correct_count = 0
    for rec in records:
        grades = classify_record(rec.text)
        if grades[0] != 0:
            g_count += 1
        elif len(rec.gold) > 0:
            unclassified.append(rec)
    print(g_count, "Unclassified", len(unclassified))
    search_phrase(unclassified, "grade")
    
