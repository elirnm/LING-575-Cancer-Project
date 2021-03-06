from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_selection import VarianceThreshold
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression # MaxEnt
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, VotingClassifier

'''
Eli Miller

Uses scikit-learn to classify strings of text.

To do:
- collect/label the training data (all the lines) and turn it into training tuples
- add a process for turning the test data into the correct format
- incorporate the metamap UMLS information into the data
- decide what classifier(s) to use - do some testing on dev data
- implement a voting system if I decide to use an ensemble
'''

def train(text):
    '''
    Takes a list of (string, label) tuples. The labels must be parsable as numbers;
        they cannot be words. Pre-convert any named labels before passing them to
        this method. Each tuple is one training instance. The string is used to
        create a bag of words feature vector.
    Returns a fitted vectorizer and a trained classifier.
    Currently creates a multinominal naive bayes classifier.
    '''
    count_vect = CountVectorizer()
    selector = VarianceThreshold()
    labels = [x[1] for x in text]
    lines = [x[0] for x in text]
    train_counts = count_vect.fit_transform(lines)
    train_counts = selector.fit_transform(train_counts, labels)
    eclf = VotingClassifier(estimators=[('svm', SVC()), ('maxent', LogisticRegression()), ('rf', RandomForestClassifier()), ('dt', DecisionTreeClassifier())])
    classifier = eclf.fit(train_counts, labels)
    return [count_vect, classifier, selector]

def test(trained_objects, text):
    '''
    Takes a trained classifier, a fitted vectorizer, and a list of strings to classify.
    Returns a list containing the classification of each string, in the same order as
        the given list of strings. The classifications are in index form, and must be
        converted back to strings after receiving the output of this method if you wish
        to have named labels.
    '''
    count_vect = trained_objects[0]
    classifier = trained_objects[1]
    selector = trained_objects[2]
    counts = count_vect.transform(text)
    counts = selector.transform(counts)
    pred = classifier.predict(counts)
    return list(pred)

if __name__ == "__main__":
    import sys
    text = [("presidents senators vote bill law", "1"), ("keyboard RAM memory CPU", "0")]
    count_vect, classifier = train(text)
    unktext = ["presidents and senators are people", "I need more memory in my keyboard"]
    ans = test(classifier, count_vect, unktext)
    print(ans)
