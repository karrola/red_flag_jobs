from django.urls import path
from . import views

urlpatterns = [
    path('', views.offer_form, name="offer_form"),
    path("company_score/", views.company_score, name="company_score"),
    path("company_score/wordcloud/", views.wordcloud_fragment, name="wordcloud_fragment"),
]
