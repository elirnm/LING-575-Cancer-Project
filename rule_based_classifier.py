import re

'''
Krista Watkins
Usage: call classify_record(record.text, diff_option)

0: Skip differentiation search entirely
1: Use diff_trial1
2: Use diff_trail2 (works best on the training data)

Returns array of integers 0-4
    0 for unknown (default)
'''

# Rexeges
num_str = "one|two|three|four|five|six|seven|eight|nine"
histologic_grade_rx = re.compile("histologic\\s+(grade):?", re.IGNORECASE)
nottgham_hist_score_rx = re.compile("nottingham\\s+histologic\\s+score:?", re.IGNORECASE)
# Numbers in groups 4 and 7
# comparator in group 6 (either 'of' for max, 'to' for range)
number_grade_rx = re.compile("^(at\\s*least\\s*)?(grade|g)?\\s*((\\d+|I+[XV]?|VI*|%s)\\s*((/|of|out of|to|-)\\s*(\\d+|I+[XV]?|VI*|%s))?)"%(num_str, num_str), re.IGNORECASE)
# Differentiation in groups 1 and 4. Starts at line beginning
differentiation_rx = re.compile("^(poorly|moderately|moderate|well)(\\s+(to|and)\\s+(poorly|moderately|moderate|well))?(\\s+|-)differentiated", re.IGNORECASE)
diff_anywhere_rx = re.compile("(poorly|moderately|moderate|well)(\\s+(to|and)\\s+(poorly|moderately|moderate|well))?(\\s+|-)differentiated", re.IGNORECASE)
# Words in groups 1 and 4
word_grade_rx = re.compile("^(low|intermediate|moderate|high)(\\s+(to|and)\\s+(low|intermediate|moderate|high))?", re.IGNORECASE);
# Numbers are in groups 6 and 9
# Comparator is in group 8
overall_grade_rx = re.compile("(overall\\s+grade|total\\s+score|nottingham\\s+histologic\\s+(grade|score|score-grade))\\s*-?\\s*(:)?\\s*(grade|g|score)?\\s*-?\\s*((\\d+|I+[XV]?|VI*|%s)+\\s*((/|of|out of|-|to)\\s*(\\d+|III|IV|IX|three|four|nine))?)"%num_str, re.IGNORECASE)
form_grade_rx = re.compile("_*x_*\\s*grade\\s*(\\d+|I+V?|one|two|three|four)", re.IGNORECASE)

# Regex for classify_string (don't require a match to be at the beginning of the string)
sum_rx = re.compile("\\d\\s*\+\\s*\\d\\s*\+\\s*\\d\\s*=\\s*(\\d)")
diff_rx = re.compile("(poorly|moderately|moderate|well)(\\s+(to|and)\\s+(poorly|moderately|moderate|well))?(\\s+|-)differentiated", re.IGNORECASE)
word_rx = re.compile("(low|intermediate|moderate|high)(\\s+(to|and)\\s+(low|intermediate|moderate|high))?", re.IGNORECASE)
num_rx = re.compile("(at\\s*least\\s*)?(grade|g)?\\s*((\\d+|I+[XV]?|VI*|%s)\\s*((/|of|out of|to|-)\\s*(\\d+|I+[XV]?|VI*|%s))?)"%(num_str, num_str), re.IGNORECASE)

def classify_record(rec, use_diff):
    '''
    For each record, assign attempt to assign tumor grades. The first trail
    to successfully find at least one grade wins
    
    Most of the trials are based on finding a grade following a specific header
    Later trials search for all instances of a specific type of grade indicator.
    '''
    
    # Histologic Grade:
    grades = header_trial(rec, "histologic\\s+(grade|score)\\s*:\\s*")
    if len(grades) > 0:
        return grades
    
    # Histologic Grade: (Nottingham histologic score)
    # Histologic Grade: Nottingham:
    grades = header_trial(rec, "histologic\\s+grade\\s*:?\\s*\(?nottingham\\s*(histologic)?\\s*(grade|score)?\)?\\s*:?\\s*")
    if len(grades) > 0:
        return grades
    
    # Histologic Grade: Bloom-richardson score
    grades = header_trial(rec, "histologic\\s+grade\\s*:\\s*bloom-richardson\\s+score\\s*")
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
    
    # Nottingham Histologic Grade:
    grades = header_trial(rec, "\(?nottingham\\s+(histologic)?\\s*(grade|score)\)?\\s*:?\\s*")
    if len(grades) > 0:
        return grades
    
    # Bloom-Richardson score
    grades = header_trial(rec, "\(?\\s*bloom-richardson\\s*(score)?\\s*\)?\\s*:?\\s*")
    if len(grades) > 0:
        return grades
    
    # Overall grade:
    grades = header_trial(rec, "overall\\s+grade\\s*:\\s*")
    if len(grades) > 0:
        return grades
    
    # Nuclear grade:
    grades = header_trial(rec, "nuclear\\s+grade\\s*:(\\s*nuclear\\s+grade)?\\s*")
    if len(grades) > 0:
        return grades
    
    # low/intermediate/high nuclear grade search
    grades = nuclear_trial(rec)
    if len(grades) > 0:
        return grades
    
    # low/intermediate/high grade search
    grades = grade_trial(rec)
    if len(grades) > 0:
        return grades
    
    if use_diff > 0:
        # Search for differentiation strings
        if use_diff == 1:
            grades = diff_trial1(rec)
            if len(grades) > 0:
                return grades
        elif use_diff == 2:
            grades = diff_trial2(rec)
            if len(grades) > 0:
                return grades
    
    return [0]

def header_trial(rec, regex):
    '''
    Given a regular expression representing a header (i.e. histologic grade:),
    Find all occurances of the header, and divide the record into sections
    
    Attempt to find a grade in each section
    '''
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
    
def diff_trial1(rec):
    '''
    Searches for indications of differentiation in the text. If only one
    grade is found, return that (unless it is 3). Otherwise return the
    maximum grade.
    
    "Poorly differentiated" occurs in many records with no annotated
    histologic grade
    '''
    diff_matches = diff_anywhere_rx.finditer(rec)
    undiff_matches = re.finditer("undifferentiated", rec, re.IGNORECASE)
    grades = []
    
    for match in diff_matches:
        grade = extract_word_grade(match, 1, 4)
        
        grades.append(grade)
    if len(grades) > 1:
        return [max(grades)]
    elif len(grades) == 1 and grades[0] == 3:
        return[]
    
    # A tumor can't be both differentiated and un-differentiated
    else:
        for match in undiff_matches:
            grades.append(4)

    return grades

def diff_trial2(rec):
    '''
    Searches the record for indications of differentiation. Ignores any
    strings indicating grade 3, because "Poorly differentiated" occurs in
    many records with no annotated histologic grade
    '''
    diff_matches = diff_anywhere_rx.finditer(rec)
    undiff_matches = re.finditer("undifferentiated", rec, re.IGNORECASE)
    grades = []
    
    for match in diff_matches:
        grade = extract_word_grade(match, 1, 4)
        if grade != 3:
            grades.append(grade)
    
    # A tumor can't be both differentiated and un-differentiated
    if len(grades) == 0:
        for match in undiff_matches:
            grades.append(4)

    return grades

def nuclear_trial(rec):
    '''
    Searches the record for instances of low/moderate/high nuclear grade
    '''
    matches = re.finditer("(low|intermediate|moderate|high)(\\s*to\\s+(low|intermediate|moderate|high))?\\s+nuclear\\s+grade", rec)
    grades = []
    
    for match in matches:
        grade = extract_word_grade(match, 1, 3)
        grades.append(grade)
    return grades

def grade_trial(rec):
    '''
    Searches the record for instances of low/moderate/high grade
    '''
    matches = re.finditer("(low|intermediate|moderate|high)(\\s*to\\s+(low|intermediate|moderate|high))?\\s+grade", rec)
    grades = []
    
    for match in matches:
        grade = extract_word_grade(match, 1, 3)
        grades.append(grade)
    return grades

def classify_section(section):
    '''
    Search through the section to find a grade. Preference is given to grades
    found at the beginning of the section
    '''
    # Special Case for nottingham a+b+c=y
    sum_found = re.search("\\d\\s*\+\\s*\\d\\s*\+\\s*\\d\\s*=\\s*(\\d)", section)
    if sum_found:
        return extract_number_grade(sum_found, 1, None, None)

    # Find differentiation at the beginning of the section
    differentiation_found = differentiation_rx.search(section)
    if differentiation_found:
        return extract_word_grade(differentiation_found, 1, 4)
    
    # Low/medium/high grade at section beginning
    word_grade_found = word_grade_rx.search(section)
    if word_grade_found:
        return extract_word_grade(word_grade_found, 1, 4)
    
    # Find numerical grade at the beginning of the section
    number_found = number_grade_rx.search(section)
    if number_found:
        return extract_number_grade(number_found, 4, 7, 6)

    # Look for the overall grade farther along in the section
    overall_grade_found = overall_grade_rx.search(section)
    if overall_grade_found:
        return extract_number_grade(overall_grade_found, 6, 9, 8)

    # Look for grade in form format: Overall Grade: __x__
    form_grade_found = form_grade_rx.search(section)
    if form_grade_found:
        return extract_number_grade(form_grade_found, 1, None, None)

    return 0

def classify_string(string):
    '''
    Given a string, attempt to find a tumor grade using a series of regexs
    The first regex to determine a grade wins
    '''
    # Special Case for nottingham a+b+c=y
    sum_found = sum_rx.search(string)
    if sum_found:
        return extract_number_grade(sum_found, 1, None, None)

    # Find differentiation at the beginning of the section
    differentiation_found = diff_rx.search(string)
    if differentiation_found:
        return extract_word_grade(differentiation_found, 1, 4)
    
    # Low/medium/high grade at section beginning
    word_grade_found = word_rx.search(string)
    if word_grade_found:
        return extract_word_grade(word_grade_found, 1, 4)
    
    # Find numerical grade at the beginning of the section
    number_found = num_rx.search(string)
    if number_found:
        return extract_number_grade(number_found, 4, 7, 6)


    # Look for the overall grade farther along in the section
    overall_grade_found = overall_grade_rx.search(string)
    if overall_grade_found:
        return extract_number_grade(overall_grade_found, 6, 9, 8)

    # Look for grade in form format: Overall Grade: __x__
    form_grade_found = form_grade_rx.search(string)
    if form_grade_found:
        return extract_number_grade(form_grade_found, 1, None, None)

    return 0

'''
Methods for determining integer grade from a regex match or string
'''

def extract_number_grade(match, first_num_location, second_num_location, comparator_loc):
    '''
    Returns a grade number for matches of the form x (of y), and its variations
    '''
    num_1_str = match.group(first_num_location)
    
    first_num = parse_number(num_1_str)
    
    # contains a maximum number (x / x) or (x to x)
    if second_num_location != None:
        num_2_str = match.group(second_num_location)
        if num_2_str != None:
            num_2_str = num_2_str
            second_num = parse_number(num_2_str)
            
            # Special case: pair of numbers is a range
            if comparator_loc != None:
                comparator = match.group(comparator_loc)
                if comparator == "to" or comparator == "-":
                    num = max(first_num, second_num)
                    if num > 4:
                        num = convert_from_nottingham(num)
                    return num
            if second_num not in [3, 4, 9]:
                num = max(first_num, second_num)
                if num > 4:
                    num = convert_from_nottingham(num)
                return num
            
            if second_num == 9:
                first_num = convert_from_nottingham(first_num)
        elif first_num > 4:
            first_num = convert_from_nottingham(first_num)
            
        
                
            
    # only contains one number (grade x)
    else:
        if first_num > 3:
            first_num = convert_from_nottingham(first_num) 

    return first_num

def parse_number(string):
    '''
    Returns the integer digit associated with a given string, or 0
    '''
    string = string.lower()
    
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
    '''
    Converts a given integer from a Nottingham score (3-9)
    to a histologic grade integer
    '''
    if nottingham_num < 6:
        return 1
    elif nottingham_num > 7:
        return 3
    else:
        return 2

def extract_word_grade(match, loc1, loc2):
    '''
    Given a regular expression containing a word-based histologic grade,
    return the corresponding number grade
    
    1: low/ well differentiated
    2: intermediate/ moderately differentiated
    3: high/ poorly differentiated
    '''

    grade_word = match.group(loc1)

    # for "poor to moderately" or "moderately to well"
    alternate_word = match.group(loc2)
    score = diff_to_num(grade_word)

    if alternate_word != None:
        alternate_score = diff_to_num(alternate_word)
        return max(score, alternate_score)

    else:
        return score

def diff_to_num(word):
    '''
    Given a word to indicate grade or differentiation, returns the
    corresponding integer grade
    '''
    word = word.lower()
    if word == "poorly" or word == "poor" or word == "high":
        return 3
    if word == "moderately" or word == "moderate" or word == "intermediate":
        return 2
    if word == "well" or word == "low":
        return 1
    return 0
