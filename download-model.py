import spacy
import spacy.cli

spacy.cli.download("en_core_web_lg")

model = spacy.load("en_core_web_lg")
model.to_disk("./models/en_core_web_lg")
