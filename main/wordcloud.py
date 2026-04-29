import spacy
import base64
from io import BytesIO
from wordcloud import WordCloud
from collections import Counter

nlp = spacy.load("pl_core_news_sm")

STOP_WORDS = {"firma", "praca", "rok", "raz", "ogólnie", "bardzo", "można"}

def keywords(reviews: list[str]) -> Counter:
    words = []
    for review in reviews:
        doc = nlp(review.lower())
        for token in doc:
            if (
                not token.is_stop
                and not token.is_punct
                and not token.is_space
                and len(token.text) > 2
                and token.pos_ in ("NOUN", "ADJ")
                and token.lemma_ not in STOP_WORDS
            ):
                words.append(token.lemma_)
    return Counter(words)


def generate_wordcloud(frequency: Counter) -> str:
    wordcloud = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        colormap="Purples",
        max_words=80,
    ).generate_from_frequencies(frequency)

    bufor = BytesIO()
    wordcloud.to_image().save(bufor, format="PNG")
    bufor.seek(0)

    return base64.b64encode(bufor.read()).decode("utf-8")