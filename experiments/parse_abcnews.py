import os
import string
import re
import nltk
import json

from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

def parse_abcnews(path: str):
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    lemmatizer = WordNetLemmatizer()
    soup = BeautifulSoup(open(path, encoding="utf8"), "html.parser")

    title = soup.find("h1", class_="vMjAx gjbzK tntuS eHrJ mTgUP").text
    title = re.sub(r'[^\w\s]', " ", title)
    title = [lemmatizer.lemmatize(word) for word in word_tokenize(title) if (lemmatizer.lemmatize(word.lower()) not in stopwords.words('english') and word not in string.punctuation)]

    date = soup.find("div", class_="jTKbV zIIsP ZdbeE xAPpq QtiLO JQYD").text

    text = soup.find("div", class_="xvlfx ZRifP TKoO eaKKC EcdEg bOdfO qXhdi NFNeu UyHES").text
    text = re.sub(r'[^\w\s]', " ", text)
    text = [lemmatizer.lemmatize(word.lower()) for word in word_tokenize(text) if (lemmatizer.lemmatize(word.lower()) not in stopwords.words('english') and word not in string.punctuation)]
    return title, date, text


if __name__ == "__main__":
    data = []
    for file in os.scandir("../data/manually_saved_sites"):
        if file.is_file():
            title, date, text = parse_abcnews(file.path)
            data.append({"title": title, "date": date, "text": text})
    with open("../data/parsed_sites/abcnews.json", "w") as outfile:
        json.dump(data, outfile)