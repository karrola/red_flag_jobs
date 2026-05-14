import spacy
from django.utils.html import escape
from django.utils.safestring import mark_safe

nlp = spacy.load("pl_core_news_sm")

KEYWORDS = [
    "dynamiczny zespół",
    "odporność na stres",
    "elastyczność",
    "dyspozycyjność",
    "rodzinna atmosfera",
    "praca pod presją czasu",
    "umiejętność pracy w warunkach niepewności",
    "owocowe czwartki",
    "młody, ambitny zespół",
    "nienormowany czas pracy",
    "wyzwania zamiast procedur",
    "ninja",
    "rockstar",
    "guru",
    "ewangelista",
    "wynagrodzenie uzależnione od efektów",
    "możliwość szybkiego awansu",
    "multitasking",
    "lojalność",
    "brak nudy",
    "szybkie tempo pracy",
    "samodzielność w działaniu",
    "szukanie rozwiązań, nie problemów",
    "gotowość do wyjazdów służbowych",
    "praca w nadgodzinach wliczona w kulturę firmy",
    "atrakcyjny system prowizyjny",
    "atrakcyjne rabaty",
    "praca dla pasjonatów",
    "wysoka kultura osobista",
    "odporność na krytykę",
    "umiejętność priorytetyzacji zadań",
    "praca w dynamicznie zmieniającym się otoczeniu",
    "szeroki zakres obowiązków",
    "osoba do wszystkiego",
    "prowizja bez górnego limitu",
    "brak sztywnych ram",
    "kreatywne podejście do problemów",
    "silna motywacja wewnętrzna",
    "orientacja na cel",
    "praca na wczoraj",
    "dyspozycyjność weekendowa",
    "stabilne zatrudnienie",
    "umowa zlecenie na okres próbny",
    "zarobki adekwatne do zaangażowania",
    "możliwość pracy zdalnej (po okresie wdrożenia)",
    "klimat startupowy",
    "płaska struktura",
    "brak korporacyjnych sztywnych zasad",
    "szukamy ludzi z 'drivem'",
    "umiejętność radzenia sobie z trudnym klientem",
    "zaangażowanie 110%",
    "praca w młodym gronie",
    "wszechstronność",
    "gotowość do nauki nowych rzeczy",
    "wysoka kultura pracy pod presją",
    "odporność psychiczna",
    "umiejętność pracy w chaosie",
    "pozytywne nastawienie",
    "brak barier",
    "wyjście poza strefę komfortu",
    "praca pełna wyzwań",
    "szukamy kogoś z 'iskrą'",
    "podejście 'can-do'",
    "nie boimy się ciężkiej pracy",
    "wysokie tempo",
    "elastyczne godziny pracy",
    "możliwość rozwoju w wielu kierunkach",
    "brak rutyny",
    "poczucie humoru",
    "wysoka samodyscyplina",
    "umiejętność pracy bez nadzoru",
    "dostępność pod telefonem",
    "zaangażowanie po godzinach",
    "umiejętność szybkiego uczenia się",
    "nastawienie na sukces",
    "poszukiwany lider zmian",
    "brak ograniczeń",
    "swoboda działania",
    "umiejętność pracy w stresujących sytuacjach",
    "gotowość do poświęceń",
    "ambitne cele sprzedażowe",
    "praca w firmie o ugruntowanej pozycji",
    "brak lęku przed porażką"]
COLOR = "#d95b81"

def get_lemmas(text: str) -> tuple:
    # zwraca tuple z lematem słowa
    return tuple(t.lemma_.lower() for t in nlp(text))

# lista lematów słów kluczowych
KEYWORD_LEMMAS = [get_lemmas(kw) for kw in KEYWORDS]

def highlight_keywords(text: str) -> str:
    doc = nlp(text)
    tokens = list(doc)
    highlighted = [False] * len(tokens)

    # szukamy dopasowań po lemmatach
    for kw_lemmas in KEYWORD_LEMMAS:
        kw_len = len(kw_lemmas)
        for i in range(len(tokens) - kw_len + 1):
            window = tuple(t.lemma_.lower() for t in tokens[i:i + kw_len])
            if window == kw_lemmas:
                for j in range(i, i + kw_len):
                    highlighted[j] = True

    # rekonstruujemy tekst zachowując oryginalne znaki (whitespace, interpunkcja)
    result = []
    prev_end = 0
    i = 0

    while i < len(tokens):
        token = tokens[i]
        # tekst przed tokenem (spacje, nowe linie)
        result.append(escape(text[prev_end:token.idx]))

        if highlighted[i]:
            # grupujemy kolejne podświetlone tokeny w jeden <mark>
            j = i
            while j < len(tokens) and highlighted[j]:
                j += 1
            span = text[token.idx : tokens[j - 1].idx + len(tokens[j - 1].text)]
            result.append(
                f'<mark style="background-color:{COLOR}; border-radius:3px; padding:0 2px">'
                f'{escape(span)}</mark>'
            )
            prev_end = tokens[j - 1].idx + len(tokens[j - 1].text)
            i = j
        else:
            result.append(escape(token.text))
            prev_end = token.idx + len(token.text)
            i += 1

    result.append(escape(text[prev_end:]))
    return mark_safe(''.join(result))