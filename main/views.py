from django.shortcuts import render

# Create your views here.

def offer_form(request):
    return render(request, "main/offer_form.html")


def company_score(request):
    return render(request, "main/company_score.html")
