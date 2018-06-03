#!/usr/bin/env python

"""Clean comment text for easier parsing."""

import re
import json
import sys



__author__ = ""
__email__ = ""

# Some useful data.
_CONTRACTIONS = {
    "tis": "'tis",
    "aint": "ain't",
    "amnt": "amn't",
    "arent": "aren't",
    "cant": "can't",
    "couldve": "could've",
    "couldnt": "couldn't",
    "didnt": "didn't",
    "doesnt": "doesn't",
    "dont": "don't",
    "hadnt": "hadn't",
    "hasnt": "hasn't",
    "havent": "haven't",
    "hed": "he'd",
    "hell": "he'll",
    "hes": "he's",
    "howd": "how'd",
    "howll": "how'll",
    "hows": "how's",
    "id": "i'd",
    "ill": "i'll",
    "im": "i'm",
    "ive": "i've",
    "isnt": "isn't",
    "itd": "it'd",
    "itll": "it'll",
    "its": "it's",
    "mightnt": "mightn't",
    "mightve": "might've",
    "mustnt": "mustn't",
    "mustve": "must've",
    "neednt": "needn't",
    "oclock": "o'clock",
    "ol": "'ol",
    "oughtnt": "oughtn't",
    "shant": "shan't",
    "shed": "she'd",
    "shell": "she'll",
    "shes": "she's",
    "shouldve": "should've",
    "shouldnt": "shouldn't",
    "somebodys": "somebody's",
    "someones": "someone's",
    "somethings": "something's",
    "thatll": "that'll",
    "thats": "that's",
    "thatd": "that'd",
    "thered": "there'd",
    "therere": "there're",
    "theres": "there's",
    "theyd": "they'd",
    "theyll": "they'll",
    "theyre": "they're",
    "theyve": "they've",
    "wasnt": "wasn't",
    "wed": "we'd",
    "wedve": "wed've",
    "well": "we'll",
    "were": "we're",
    "weve": "we've",
    "werent": "weren't",
    "whatd": "what'd",
    "whatll": "what'll",
    "whatre": "what're",
    "whats": "what's",
    "whatve": "what've",
    "whens": "when's",
    "whered": "where'd",
    "wheres": "where's",
    "whereve": "where've",
    "whod": "who'd",
    "whodve": "whod've",
    "wholl": "who'll",
    "whore": "who're",
    "whos": "who's",
    "whove": "who've",
    "whyd": "why'd",
    "whyre": "why're",
    "whys": "why's",
    "wont": "won't",
    "wouldve": "would've",
    "wouldnt": "wouldn't",
    "yall": "y'all",
    "youd": "you'd",
    "youll": "you'll",
    "youre": "you're",
    "youve": "you've"
}

# You may need to write regular expressions.

def sanitize(text):
    """Do parse the text in variable "text" according to the spec, and return
    a LIST containing FOUR strings
    1. The parsed text.
    2. The unigrams
    3. The bigrams
    4. The trigrams
    """

    # YOUR CODE GOES BELOW:
    unigrams = bigrams = trigrams = ""

    #Replace new line and tab
    parsed_text = text.replace('\n', ' ')
    parsed_text = parsed_text.replace('\t', ' ')

    #Remove all URLs
    http_pos = parsed_text.find('http')
    while (http_pos != -1):
        space_pos = parsed_text[http_pos+1:].find(' ')
        if (space_pos != -1):
            parsed_text = parsed_text[:http_pos] + parsed_text[http_pos+space_pos+2:]
        else:
            parsed_text = parsed_text[:http_pos]
        http_pos = parsed_text.find('http')

    #Remove all parenthesis and quote
    parsed_text = parsed_text.replace('(', ' ')
    parsed_text = parsed_text.replace(')', ' ')
    parsed_text = parsed_text.replace('[', ' ')
    parsed_text = parsed_text.replace(']', ' ')
    parsed_text = parsed_text.replace('{', ' ')
    parsed_text = parsed_text.replace('}', ' ')
    parsed_text = parsed_text.replace('"', ' ')
    parsed_text = parsed_text.replace('“', ' ')
    parsed_text = parsed_text.replace('”', ' ')

    # Remove duplicate space and change to lower case
    parsed_text = ' '.join(parsed_text.split())
    parsed_text = parsed_text.lower()

    #Separate all external punctuation
    pattern = re.compile('[^a-zA-Z0-9\s\*\+\|\^\$\\\]\s')
    punctuation_list = pattern.findall(parsed_text)
    punctuation_list = list(set(punctuation_list))
    for i in range(len(punctuation_list)):
        punctuation = punctuation_list[i][0]
        replace = ' '+punctuation
        if (punctuation == "?"):
            punctuation = "\?"
            replace = " ? "
        elif (punctuation == "."):
            punctuation = "\."
            replace = " . "
        parsed_text = re.sub(punctuation, replace, parsed_text)

    if re.search('[^a-zA-Z0-9\s]', parsed_text[-1:]) != None:
        i = -1
        parsed_text = parsed_text[:-1] + ' ' + parsed_text[-1:]
    #Remove all punctuation except punctuation that ends a phrase or sentence.
    pattern = re.compile('[^a-zA-Z0-9\s\.!\?,;:]\s')
    remove_list = pattern.findall(parsed_text)
    remove_list = list(set(remove_list))
    for i in range(len(remove_list)):
        parsed_text = parsed_text.replace(remove_list[i][0], '')

    pattern = re.compile('\s[^a-zA-Z0-9\s\.!\?,;:]')
    remove_list = pattern.findall(parsed_text)
    remove_list = list(set(remove_list))
    for i in range(len(remove_list)):
        parsed_text = parsed_text.replace(remove_list[i][1], '')

    #Parse the string to sentences
    parsed_list = re.split(r"[\.!\?,;:]", parsed_text)
    for i in range(len(parsed_list)):
        parsed_list[i] = ' '.join(parsed_list[i].split())

    parsed_text = ' '.join(parsed_text.split())

    #Create unigrams
    unigrams = ' '.join(parsed_list)
    unigrams = ' '.join(unigrams.split())

    #Create bigrams
    bigrams_list = []
    for sent in parsed_list:
        if (sent.count(' ') > 0):
            curr_space = sent.find(' ')
            next_space = sent[curr_space+1:].find(' ')

            while (next_space != -1):
                bigrams_list.append(sent[:curr_space] + '_' +
                                    sent[curr_space + 1: curr_space+next_space+1])
                sent = sent[curr_space+1:]
                curr_space = sent.find(' ')
                next_space = sent[curr_space + 1:].find(' ')

            bigrams_list.append(sent[:curr_space] + '_' + sent[curr_space + 1:])

    bigrams = ' '.join(bigrams_list)
    bigrams = ' '.join(bigrams.split())

    #Create trigrams
    trigrams_list = []
    for sent in parsed_list:
        if (sent.count(' ') > 1):
            curr_space = sent.find(' ')
            next_space = sent[curr_space + 1:].find(' ')
            third_space = sent[curr_space+next_space+2:].find(' ')

            while (third_space != -1):
                trigrams_list.append(sent[:curr_space] + '_' +
                        sent[curr_space + 1: curr_space + next_space + 1] + '_' +
                        sent[curr_space+ next_space + 2: curr_space + next_space+ third_space + 2])
                sent = sent[curr_space + 1:]
                curr_space = sent.find(' ')
                next_space = sent[curr_space + 1:].find(' ')
                third_space = sent[curr_space + next_space + 2:].find(' ')

            trigrams_list.append(sent[:curr_space] + '_' +
                            sent[curr_space + 1: curr_space+next_space] + '_' +
                            sent[curr_space + next_space + third_space + 3:])

    trigrams = ' '.join(trigrams_list)
    trigrams = ' '.join(trigrams.split())



    return [parsed_text, unigrams, bigrams, trigrams]


if __name__ == "__main__":
    # This is the Python main function.
    # You should be able to run
    # python cleantext.py <filename>
    # and this "main" function will open the file,
    # read it line by line, extract the proper value from the JSON,
    # pass to "sanitize" and print the result as a list.

    # YOUR CODE GOES BELOW.

    # prompt the user for a file to import

    filename = sys.argv[1]
    print(sys.argv[1])

    #filename =  './test.json'
    # Read JSON data into the datastore variable
    if filename:
        with open(filename, encoding='utf-8') as fd:
            json_str = fd.readline()
            while (json_str != ""):
                data = json.loads(json_str)
                print(data['body'])
                s = sanitize(data['body'])
                for x in s:
                    print(x)
                print('\n')
                json_str = fd.readline()


