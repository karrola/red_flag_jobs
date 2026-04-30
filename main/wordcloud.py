import spacy
import base64
from io import BytesIO
from wordcloud import WordCloud
from collections import Counter
import matplotlib.pyplot as plt

nlp = spacy.load("pl_core_news_sm")

STOP_WORDS = {
    "firma", "praca", "rok", "raz", "ogólnie", "bardzo", "można", "pracownik", "osoba",
    "być", "mieć", "móc", "chcieć", "trzeba", "należy", "powinien", "może", "jest", "są",
    "dzień", "tydzień", "miesiąc", "czas", "często", "zawsze", "nigdy", "dużo", "mało", "wiele", "kilka",
    "ok", "okej", "spoko", "średnio", "raczej",
    "wgl", "trochę", "poprostu", "troche", "trochę", "jakby", "troche", "no", "także", "wtedy",
    "ja", "ty", "on", "ona", "my", "wy", "oni", "to", "ten", "ta", "te", "taki", "taka", "takie",
    "ale", "bo", "więc", "dlatego", "ponieważ", "jednak", "chociaż", "mimo", "oraz", "lub",
    "rekrutacja", "aplikacja", "cv", "rozmowa", "umowa", "szef", "kierownik", "manager", "zespół", "hr", "rekruter",
    "moim", "zdaniem", "uważam", "myślę", "wydaje", "się", "mi", "ci", "nam", "wam", "budynek", "biuro", "pokój", "sala", "kuchnia", "łazienka", "toaleta", "parking", "windy",
    "rodzina", "rodzice", "partner", "żona", "mąż", "dzieci", "syn", "córka", "znajomi", "przyjaciele",
    "stanowisko", "specjalista", "analityk", "asystent", "koordynator", "kierownik", "dyrektor",
    "chyba", "może", "raczej", "prawdopodobnie", "wydaje", "właściwie", "zazwyczaj",
    "zawsze", "nigdy", "czasami", "niekiedy", "rzadko", "codziennie", "każdy", "wszystko", "wszyscy",
     "administracja", "administracyjny", "formalności", "dokumenty", "papiery", "procedury",
    "troszkę", "troszeczkę", "dosyć", "wystarczająco", "całkiem", "zupełnie", "niemal", "prawie",
    "tak", "nie", "raczej", "może", "pewnie", "owszem", "no", "hm", "aha", "no",
    "proszę", "dziękuję", "przepraszam", "witam", "do widzenia",
    "zrobić", "zrobił", "zrobiła", "zrobili", "robimy", "robili", "zostać", "stać",
    "biuro", "gabinet", "hol", "korytarz", "schody", "windy", "magazyn", "hala",
    "kawa", "herbata", "obiad", "śniadanie", "przerwa", "lunch", "posiłek", "napój",
    "komputer", "laptop", "monitor", "klawiatura", "mysz", "drukarka", "skaner", "telefon",
    "umowa", "kontrakt", "porozumienie", "warunki", "zapis", "paragraf", "punkt",
    "młody", "stary", "nowy", "stary", "doświadczony", "początkujący", "starszy",
    "dwa", "trzy", "cztery", "pięć", "sześć", "siedem", "osiem", "dziewięć", "dziesięć",
    "pierwszy", "drugi", "trzeci", "ostatni", "następny", "poprzedni",
    "ponoć", "podobno", "rzekomo", "teoretycznie", "praktycznie", "zasadniczo",
    "naprawdę", "faktycznie", "istotnie", "rzeczywiście", "oczywiście", "naturalnie",
    "właśnie", "no właśnie", "kurczę", "kurde", "cholera", "jasne", "spoko", "luźno",
    "godzina", "harmonogram", "grafik", "zmiana", "zmiany", "zmianowy",
    "etat", "wymiar czasu", "norma", "normy", "poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela",
    "weekend", "weekendy", "rano", "południe", "popołudnie", "wieczór", "noc", "ranek", "wieczorem", "nocą", "kształcenie", "kształcenia", "edukacja", "edukacji", "nauka", "nauki",
    "szkolenie", "szkolenia", "kursy", "kursów", "akademia",
    "rozwój", "rozwoju", "podnoszenie kwalifikacji", "dokształcanie", "informatyka", "informatyki", "informatyczny", "informatyczne",
    "technologia", "technologie", "oprogramowanie", "system", "systemy", "wydział", "wydziału", "wydziale", "jednostka", "departament", 
    "dział", "sekcja", "oddział", "filia", "swoja"

}

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
                and token.pos_ != "PROPN" 
                and token.lemma_ not in STOP_WORDS
            ):
                words.append(token.lemma_)
    return Counter(words)


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