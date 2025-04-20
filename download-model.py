import spacy
import spacy.cli
from transformers import AutoModel

try:
    spacy.load("./models/en_core_web_lg")
except:
    spacy.cli.download("en_core_web_lg")
    model = spacy.load("en_core_web_lg")
    model.to_disk("./models/en_core_web_lg")
finally:
    print("spacy model is ready")


AutoModel.from_pretrained(
    pretrained_model_name_or_path="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli", cache_dir="./models/cache"
)
