from urllib.parse import urlencode

from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.cache import cache
from .scraper import get_reviews
from .wordcloud import keywords, generate_wordcloud
from .highlight_keywords import highlight_keywords
import hashlib

def offer_form(request):
    if request.method == "POST":
        company = request.POST.get("company", "").strip()
        position = request.POST.get("position", "").strip()

        request.session["company"] = company
        request.session["position"] = position
        request.session["gowork_url"] = request.POST.get("gowork_url", "").strip()
        request.session["offer_text"] = request.POST.get("offer", "").strip()

        query = urlencode({"company": company, "position": position})
        return redirect(f"{reverse('company_score')}?{query}")

    return render(request, "main/offer_form.html")

def company_score(request):
    company = request.GET.get("company", request.session.get("company", ""))
    position = request.GET.get("position", request.session.get("position", ""))

    return render(request, "main/company_score.html", {
        "company": company,
        "position": position,
        "gowork_url": request.session.get("gowork_url", ""),
    })

def offer_analysis(request):
    offer_text = request.session.get("offer_text", "")
    text_hash = hashlib.md5(offer_text.encode()).hexdigest()
    cache_key = f"offer_highlights_{text_hash}"

    cached = cache.get(cache_key)

    if cached:
        highlighted_text = cached["highlighted_text"]
        detections = cached["detections"]
    else:
        highlighted_text, detections = highlight_keywords(offer_text) if offer_text else (None, [])
        cache.set(cache_key, {"highlighted_text": highlighted_text, "detections": detections}, timeout=60 * 60)

    return render(request, 'main/offer_analysis.html', {
        "highlighted_text": highlighted_text,
        "detections": detections,
    })


def wordcloud_fragment(request):
    gowork_url = request.GET.get("gowork_url", "")

    if not gowork_url:
        return render(request, "main/wordcloud.html")

    url_hash = hashlib.sha256(gowork_url.encode()).hexdigest()
    cache_key = f"wordcloud:{url_hash}"

    wordcloud_b64 = cache.get(cache_key)

    if not wordcloud_b64:
        reviews = get_reviews(gowork_url)
        frequency = keywords(reviews)
        wordcloud_b64 = generate_wordcloud(frequency)
        cache.set(cache_key, wordcloud_b64, timeout=60 * 60)

    return render(request, "main/wordcloud.html", {"wordcloud": wordcloud_b64})
