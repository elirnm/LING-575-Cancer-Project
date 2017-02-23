from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

def train(text):
    '''
    Takes a list of (line, label) tuples.
    Returns a fitted vectorizer and a trained classifier.
    '''
    count_vect = CountVectorizer()
    labels = [x[1] for x in text]
    lines = [x[0] for x in text]
    train_counts = count_vect.fit_transform(lines)
    print(train_counts.shape)
    mnb = MultinomialNB().fit(train_counts, labels)
    return count_vect, mnb

def test(model, count_vect, text):
    '''
    Takes a trained classifier, a fitted vectorizer, and a list of strings to classify.
    Returns a list containing the classification of each string, in the same order as
    the given list of strings.
    '''
    counts = count_vect.transform(text)
    pred = model.predict(counts)
    return list(pred)

if __name__ == "__main__":
    import sys
    text = [("presidents senators vote bill law", "1"), ("keyboard RAM memory CPU", "0")]
    count_vect, model = train(text)
    unktext = ["presidents and senators are people", "I need more memory in my keyboard"]
    ans = test(model, count_vect, unktext)
    print(ans)
