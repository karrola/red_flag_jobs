from django.shortcuts import render, redirect
from .scraper import get_reviews
from .wordcloud import keywords, generate_wordcloud
from django.core.cache import cache


URL_GOWORK = "https://www.gowork.pl/opinie_czytaj,19205"

# Create your views here.

def offer_form(request):
    if request.method == "POST":
        request.session["gowork_url"] = request.POST.get("gowork_url", "")
        return redirect("company_score")
    
    return render(request, "main/offer_form.html")

def company_score(request):
    gowork_url = request.session.get("gowork_url", "")
    return render(request, "main/company_score.html", {"gowork_url": gowork_url})

def wordcloud_fragment(request):
    gowork_url = request.GET.get("gowork_url", "")

    if not gowork_url:
        return render(request, "main/wordcloud.html")
    
    # wordcloud_b64 = cache.get("gowork_url")

    # if not wordcloud_b64:
    reviews = get_reviews(gowork_url)
    frequency = keywords(reviews)
    wordcloud_b64 = generate_wordcloud(frequency)
    cache.set("gowork_wordcloud", wordcloud_b64, timeout=60 * 60)

    return render(request, "main/wordcloud.html", {"wordcloud": wordcloud_b64})