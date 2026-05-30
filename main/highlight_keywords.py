from collections import defaultdict
from html import escape
import spacy
from sentence_transformers import SentenceTransformer, util
from django.utils.safestring import mark_safe
from .keyword_groups import KEYWORD_GROUPS

nlp = spacy.load("pl_core_news_sm")

COLOR = "#d95b81" # kolor podświetlenia
SIMILARITY_THRESHOLD = 0.83 # minimalny próg pododbieństwa dla dopasowania semantycznego
MAX_WINDOW_TOKENS = 30  # maksymalna długość sprawdzanych spanów
GROUP_MARGIN = 0.08   # minimalny margines między najlepszą a drugą grupą
TOP_K = 2             # ile top keywordów bierzemy do uśrednienia


def get_lemmas(text: str) -> tuple:
    # zwraca krotkę lematów dla podanego tekstu
    return tuple(t.lemma_.lower() for t in nlp(text))

# zamieniamy strukturę grup słów kluczowych na jedną płaską listę wpisów
KEYWORD_ENTRIES = []

for _group_id, _group in enumerate(KEYWORD_GROUPS):
    for _phrase in _group["phrases"]:
        KEYWORD_ENTRIES.append({
            "phrase": _phrase,
            "translation": _group["translation"],
            "group_id": _group_id,
            "lemmas": get_lemmas(_phrase),
        })

# ładujemy model do dopasowania semantycznego
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

# zamieniamy frazy na wektory
KEYWORD_EMBEDDINGS = model.encode(
    [entry["phrase"] for entry in KEYWORD_ENTRIES],
    convert_to_tensor=True,
)

# słownik grup fraz: id_grupy: lista fraz
_groups_phrases: dict[int, list[str]] = defaultdict(list)
for _entry in KEYWORD_ENTRIES:
    _groups_phrases[_entry["group_id"]].append(_entry["phrase"])

# słownik grup embeddingów fraz
GROUP_EMBEDDINGS: dict[int, object] = {
    group_id: model.encode(phrases, convert_to_tensor=True)
    for group_id, phrases in _groups_phrases.items()
}


def highlight_keywords(text: str) -> tuple[str, list[dict]]:
    """
    Wykrywa keywordy w tekście na dwa sposoby:
    1) dopasowanie lematyczne,
    2) dopasowanie semantyczne.

    Zwraca:
    - HTML z podświetleniami,
    - listę wykrytych trafień (detections).
    """
    doc = nlp(text)
    tokens = list(doc)

    # lista w której oznaczamy czy dany token został oznaczony
    token_detection_ids = [None] * len(tokens)

    # lista wszystkich wykrytych trafień
    detections: list[dict] = []

    def add_detection(
        start: int,
        end: int,
        matched_text: str,
        normalized_text: str,
        translation: str,
        match_type: str,
        similarity: float,
        keyword_phrase: str,
        group_id: int,
    ) -> None:
        """
        Dodaje jedno wykrycie do listy detections i oznacza należące do niego tokeny.
        """
        detection_id = len(detections)
        detections.append({
            "id": detection_id,
            "start": start, # indeks start
            "end": end, # indeks oniec
            "matched_text": matched_text, # dokładny tekst
            "normalized_text": normalized_text,
            "translation": translation,
            "match_type": match_type, # lemma albo semantic
            "similarity": round(float(similarity), 3),
            "keyword_phrase": keyword_phrase, # oryginalna fraza keyworda
            "group_id": group_id,
        })

        # oznaczamy wszystkie tokeny należące do tego trafienia
        for i in range(start, end):
            token_detection_ids[i] = detection_id

    # DOPASOWANIE LEMATYCZNE
    # szukamy dosłownych dopasowań po lematyzacji

    for entry in KEYWORD_ENTRIES:
        kw_lemmas = entry["lemmas"]
        kw_len = len(kw_lemmas)

        for i in range(len(tokens) - kw_len + 1):
            # jeśli którykolwiek token w oknie już należy do innego wykrycia, pomijamy
            if any(x is not None for x in token_detection_ids[i:i + kw_len]):
                continue
            
            # po kolei sprawdzamy lematy długośći danej frazy i sprawdzamy czy są równe lematom tej frazy
            window = tuple(t.lemma_.lower() for t in tokens[i:i + kw_len])

            if window == kw_lemmas:
                span_start = tokens[i].idx
                span_end = tokens[i + kw_len - 1].idx + len(tokens[i + kw_len - 1].text)

                add_detection(
                    start=i,
                    end=i + kw_len,
                    matched_text=text[span_start:span_end],
                    normalized_text=entry["phrase"],
                    translation=entry["translation"],
                    match_type="lemma",
                    similarity=1.0,
                    keyword_phrase=entry["phrase"],
                    group_id=entry["group_id"],
                )

    # DOPASOWANIE SEMANTYCZNE
    # Najpierw sprawdzamy, które zdania wyglądają na potencjalnie interesujące.
    # Potem generujemy kandydatów-spanów i porównujemy ich embeddingi z keywordami.

    # dzielimy tekst na zdania żeby analizować frazy w kontekście zdań
    sentences = list(doc.sents)

    sent_embeddings = model.encode(
        [s.text for s in sentences],
        convert_to_tensor=True,
        batch_size=64,
        show_progress_bar=False,
    )

    # dla każdego zdania bierzemy najlepsze dopasowanie do dowolnego keyworda
    sent_sims = util.cos_sim(sent_embeddings, KEYWORD_EMBEDDINGS).max(dim=1).values

    # zostawiamy tylko zdania które osiągnęły minimalny próg podobieństwa, żeby nie analizowac dalej wszystkich
    suspicious_sents = {
        i for i, sim in enumerate(sent_sims)
        if sim.item() > 0.55
    }

    # lista spanów do sprawdzenia
    candidates = []
    # już widziane spany
    seen_spans = set()

    for sent_idx, sent in enumerate(sentences):
        if sent_idx not in suspicious_sents:
            continue

        sent_tokens = list(sent)
        offset = sent.start

        # szukamy spanów  od najdłuższych do najkrótszych
        for window_size in range(MAX_WINDOW_TOKENS, 1, -1):
            for i in range(len(sent_tokens) - window_size + 1):
                # globalny indeks, później potrzebny do detection
                global_i = offset + i
                global_end = global_i + window_size

                # jeżeli span nachodzi na już wykryte trafienie to go pomijamy
                if any(x is not None for x in token_detection_ids[global_i:global_end]):
                    continue

                span_tokens = sent_tokens[i:i + window_size]

                # odrzucamy same spacje, interpunkcję i liczby
                if any(t.is_space for t in span_tokens):
                    continue
                if any(t.like_num for t in span_tokens):
                    continue
                if sent_tokens[i].is_punct or sent_tokens[i + window_size - 1].is_punct:
                    continue
                if all(not t.text.strip().isalnum() for t in span_tokens):
                    continue

                # wycinamy dokładny tekst 
                span_text = text[
                    sent_tokens[i].idx:
                    sent_tokens[i + window_size - 1].idx + len(sent_tokens[i + window_size - 1].text)
                ]

                clean_span = span_text.strip()

                if len(clean_span) < 3:
                    continue
                if not any(c.isalpha() for c in clean_span):
                    continue
                if all(not c.isalnum() for c in clean_span):
                    continue

                # zapamiętujemy już widziane spany
                key = clean_span.lower()
                if key in seen_spans:
                    continue
                seen_spans.add(key)

                candidates.append((global_i, global_end, span_text))

    if candidates:
        span_texts = [c[2] for c in candidates]
        
        # embeddingi kandydatów
        span_embeddings = model.encode(
            span_texts,
            convert_to_tensor=True,
            batch_size=64,
            show_progress_bar=False,
        )

        # podobieństwo spanu do każdego keyworda, wybieram k najlepszych i usredniam wynik, zapamiętuję indeks najlepszego keyworda (później do wybrania tłumaczenia)
        similarities = util.cos_sim(span_embeddings, KEYWORD_EMBEDDINGS)
        topk = similarities.topk(min(TOP_K, similarities.shape[1]), dim=1)
        max_sims = topk.values.mean(dim=1)
        best_keyword_idx = topk.indices[:, 0]

        # dla każdego spanu liczymy podobieństwo do najlepszej frazy z każdej grupy
        group_ids_ordered = sorted(GROUP_EMBEDDINGS.keys())
        group_max_sims_per_span = []

        for group_id in group_ids_ordered:
            grp_embs = GROUP_EMBEDDINGS[group_id]
            grp_sim = util.cos_sim(span_embeddings, grp_embs).max(dim=1).values
            group_max_sims_per_span.append(grp_sim)

        # przechodzimy po wszystkich kandydatach i decydujemy czy dany span ma być uznany za trafienie
        for idx, (start, end, span_text) in enumerate(candidates):
            sim = max_sims[idx].item()

            # sprawdzamy czy najlepsza grupa wygrywa wyraźnie z drugą najlepszą
            group_scores = {
                group_id: group_max_sims_per_span[pos][idx].item()
                for pos, group_id in enumerate(group_ids_ordered)
            }
            sorted_scores = sorted(group_scores.values(), reverse=True)

            if len(sorted_scores) >= 2:
                margin = sorted_scores[0] - sorted_scores[1]
                if margin < GROUP_MARGIN:
                    continue  # span niejednoznaczny – odpada

            # wyłaniamy zwycięską grupę i wybieramy z niej najlepszy keyword
            winning_group_id = max(group_scores, key=group_scores.get)
            winning_group_entries = [
                e for e in KEYWORD_ENTRIES if e["group_id"] == winning_group_id
            ]
            grp_sims = util.cos_sim(
                span_embeddings[idx].unsqueeze(0),
                GROUP_EMBEDDINGS[winning_group_id],
            )[0]
            best_in_group = winning_group_entries[grp_sims.argmax().item()]

            # używamy podobieństwa do zwycięskiej grupy jako miary pewności
            sim = group_scores[winning_group_id]

            span_len = len(span_text.split())

            # krótkie spany wymagają większej pewności
            if span_len < 3 and sim < 0.88:
                continue

            # lekki boost dla dłuższych spanów
            boost = min(span_len / 4, 1.25)
            sim = sim * boost

            if sim >= SIMILARITY_THRESHOLD:
                add_detection(
                    start=start,
                    end=end,
                    matched_text=span_text,
                    normalized_text=best_in_group["phrase"],
                    translation=best_in_group["translation"],
                    match_type="semantic",
                    similarity=sim,
                    keyword_phrase=best_in_group["phrase"],
                    group_id=winning_group_id,
                )

    # łączymy detekcje, jeśli:
    # - są blisko siebie,
    # - przerwa między nimi jest nieistotna,
    # - mają ten sam translation.

    if detections:
        detections.sort(key=lambda d: d["start"])

        merged = []
        skip = set()

        for i, det in enumerate(detections):
            if i in skip:
                continue

            current = det.copy()

            for j in range(i + 1, len(detections)):
                if j in skip:
                    continue

                d = detections[j]

                gap_tokens = tokens[current["end"]:d["start"]]
                gap_size = d["start"] - current["end"]

                gap_is_trivial = (
                    gap_size <= 3
                    and all(t.is_stop or t.is_punct or t.is_space for t in gap_tokens)
                )

                if not gap_is_trivial:
                    break

                if d["translation"] == current["translation"]:
                    for k in range(i + 1, j + 1):
                        skip.add(k)

                    span_start = tokens[current["start"]].idx
                    span_end = tokens[d["end"] - 1].idx + len(tokens[d["end"] - 1].text)
                    current["end"] = d["end"]
                    current["matched_text"] = text[span_start:span_end]
                    current["similarity"] = max(current["similarity"], d["similarity"])

            merged.append(current)

        # po scaleniu przebudowujemy ID detekcji i mapowanie tokenów.
        new_detections = []
        token_detection_ids = [None] * len(tokens)

        for new_id, d in enumerate(merged):
            d["id"] = new_id
            new_detections.append(d)
            for i in range(d["start"], d["end"]):
                token_detection_ids[i] = new_id

        detections = new_detections

    # sklejamy wynikowy tekst, a wykryte fragmenty owijamy w <mark>.

    result = []
    prev_end = 0
    i = 0

    while i < len(tokens):
        token = tokens[i]

        # dodajemy wszystko co było przed bieżącym tokenem
        result.append(escape(text[prev_end:token.idx]))

        detection_id = token_detection_ids[i]

        # jeżeli token nie należy do żadnego trafienia dodajemy go zwyczajnie
        if detection_id is None:
            result.append(escape(token.text))
            prev_end = token.idx + len(token.text)
            i += 1
            continue

        # jeśli token należy do detekcji znajdujemy cały spójny span tej detekcji
        j = i
        while j < len(tokens) and token_detection_ids[j] == detection_id:
            j += 1

        det = detections[detection_id]

        span_start = tokens[i].idx
        span_end = tokens[j - 1].idx + len(tokens[j - 1].text)
        span = text[span_start:span_end]

        # tworzymy podświetlony html
        result.append(
            f'<mark '
            f'style="background-color:{COLOR}; border-radius:3px; padding:0 2px" '
            f'data-translation="{escape(det["translation"])}" '
            f'data-match-text="{escape(det["matched_text"])}" '
            f'data-match-type="{escape(det["match_type"])}" '
            f'title="{escape(det["translation"])}">'
            f'{escape(span)}'
            f'</mark>'
        )

        prev_end = span_end
        i = j

    # dodajemy końcówkę tekstu po ostatnim tokenie
    result.append(escape(text[prev_end:]))

    return mark_safe("".join(result)), detections