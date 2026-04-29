from django.shortcuts import render
from .scraper import get_reviews
from .wordcloud import keywords, generate_wordcloud
from django.core.cache import cache


URL_GOWORK = "https://www.gowork.pl/opinie_czytaj,19205"

# Create your views here.

def offer_form(request):
    return render(request, "main/offer_form.html")

def company_score(request):
    return render(request, "main/company_score.html")

def wordcloud_fragment(request):
    wordcloud_b64 = cache.get("gowork_wordcloud")

    if not wordcloud_b64:
        reviews = get_reviews(URL_GOWORK)
        frequency = keywords(reviews)
        wordcloud_b64 = generate_wordcloud(frequency)
        cache.set("gowork_wordcloud", wordcloud_b64, timeout=60 * 60)

    return render(request, "main/wordcloud.html", {"wordcloud": wordcloud_b64})