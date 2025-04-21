import os

os.environ["HF_HOME"] = "./models/cache"

import spacy
import spacy.cli
from transformers import pipeline

spacy_model = "en_core_web_lg"

try:
    spacy.load(f"./models/{spacy_model}")
except:
    spacy.cli.download(spacy_model)
    model = spacy.load(spacy_model)
    model.to_disk(f"./models/{spacy_model}")
finally:
    print("spacy model is ready")

tf_model = "facebook/bart-large-mnli"

pipeline("zero-shot-classification", model=tf_model)
