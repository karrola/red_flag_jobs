import spacy
import base64
from io import BytesIO
from wordcloud import WordCloud
from collections import Counter
import matplotlib.pyplot as plt
from nltk.util import ngrams

nlp = spacy.load("pl_core_news_sm")

STOP_WORDS = {
    # Czasowniki generyczne (VERB)
    "być", "mieć", "móc", "chcieć", "trzeba", "należy", "powinien",
    "zrobić", "robić", "zostać", "stać",

    # Przymiotniki generyczne (ADJ)
    "nowy", "stary", "doświadczony", "początkujący", "starszy", "młody",
    "taki", "każdy",

    # Rzeczowniki zbyt ogólne (NOUN)
    "firma", "praca", "pracownik", "osoba", "rok", "raz",
    "rekrutacja", "aplikacja", "rozmowa", "umowa", "kontrakt", "warunki",
    "szef", "kierownik", "manager", "zespół", "rekruter",
    "stanowisko", "specjalista", "analityk", "asystent", "koordynator", "dyrektor",
    "dzień", "tydzień", "miesiąc", "czas", "godzina", "harmonogram", "grafik", "zmiana", "etat",
    "poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela", "weekend",
    "biuro", "gabinet", "budynek", "pokój", "sala", "kuchnia", "korytarz", "magazyn", "parking",
    "komputer", "laptop", "monitor", "klawiatura", "drukarka", "skaner", "telefon",
    "kawa", "herbata", "obiad", "śniadanie", "przerwa", "lunch", "posiłek", "napój",
    "administracja", "formalność", "dokument", "papier", "procedura",
    "szkolenie", "kurs", "akademia", "edukacja", "nauka", "kształcenie",
    "technologia", "oprogramowanie", "system", "informatyka",
    "wydział", "jednostka", "departament", "dział", "sekcja", "oddział",
    "rodzina", "rodzic", "partner", "znajomy", "przyjaciel",
    "firma", "praca", "pracownik", "osoba", "rok", "raz",
    "człowiek", "ludzie", "kolega", "koleżanka", "pracodawca", "zatrudniony",
    "rekruter", "szef", "kierownik", "manager", "koordynator", "dyrektor",
    "specjalista", "analityk", "asystent", "administrator", "informatyk",
    "stażysta", "praktykant", "konsultant", "ekspert",
}

ALLOWED_POS = ["NOUN", "ADJ", "VERB"]

def keywords(reviews: list[str]) -> Counter:
    words = []
    bigrams = []
    for review in reviews:
        doc = nlp(review.lower())
        
        valid_tokens = [
            t for t in doc
            if not t.is_stop
            and not t.is_punct
            and len(t.text) > 2
            and t.pos_ in ALLOWED_POS
            and t.lemma_ not in STOP_WORDS
        ]
        
        words.extend(t.lemma_ for t in valid_tokens)
        bigrams.extend(
            " ".join(t.text for t in b) 
            for b in ngrams(valid_tokens, 2)
        )

    word_counts = Counter(words)
    bigram_counts = Counter(bigrams) 

    for key in bigram_counts:
        bigram_counts[key] *= 2

    return word_counts + bigram_counts

def color_func(*args, **kwargs):
    cmap = plt.cm.Purples
    import random
    return "rgba({}, {}, {}, 1)".format(
        *[int(x * 255) for x in cmap(random.uniform(0.4, 0.9))[:3]]
    )

def generate_wordcloud(frequency: Counter) -> str:
    wordcloud = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        color_func=color_func,
        max_words=80,
    ).generate_from_frequencies(frequency)

    bufor = BytesIO()
    wordcloud.to_image().save(bufor, format="PNG")
    bufor.seek(0)

    return base64.b64encode(bufor.read()).decode("utf-8")