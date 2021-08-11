from .models import *
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView, UpdateView, DetailView, ListView, DeleteView, View, TemplateView

def index(request):
    article_tout = Article.objects.all()
    brouillons = article_tout.filter(published=False)
    publications = article_tout.filter(published=True)
    context = {
        'brouillons':brouillons,
        'publications':publications
    }
    return render(request, 'journal/accueil.html', context)

class ArticleDetailView(DetailView):
    model = Article
    template_name = "journal/crud/article_details.html"

class ArticleCreateView(CreateView, LoginRequiredMixin, SuccessMessageMixin):
    model = Article
    fields = '__all__'
    template_name = "journal/crud/article_ajout.html"

class ArticleUpdateView(UpdateView, LoginRequiredMixin, SuccessMessageMixin):
    model = Article
    fields = '__all__'
    template_name = "journal/crud/article_ajout.html"

class ArticleDeleteView(DeleteView, LoginRequiredMixin, SuccessMessageMixin):
    model = Article
    template_name = "journal/crud/objet_a_effacer.html"
    success_url = '/journal/'