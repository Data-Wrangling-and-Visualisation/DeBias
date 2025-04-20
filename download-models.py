import spacy
import spacy.cli
from transformers import AutoModel, AutoTokenizer

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

AutoModel.from_pretrained(
    pretrained_model_name_or_path=tf_model,
    cache_dir="./models/cache/model",
)

AutoTokenizer.from_pretrained(
    pretrained_model_name_or_path=tf_model,
    cache_dir="./models/cache/tokenizer",
)
