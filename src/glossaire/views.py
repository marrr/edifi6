from .models import *
from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse_lazy
from django.forms.widgets import CheckboxSelectMultiple
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import View, CreateView, ListView, DetailView, UpdateView, DeleteView

class TermeListView(ListView):
    model = Terme
    template_name = "glossaire/accueil.html"

class TermeDetailView(DetailView, LoginRequiredMixin, SuccessMessageMixin):
    model = Terme
    template_name = "glossaire/crud/terme_details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['termes_lies'] = self.object.tags.similar_objects()
        return context

class TermeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Terme
    fields = '__all__'
    success_message = "Terme ajouté au glossaire. Merci."
    template_name = "glossaire/crud/terme_ajout.html"

class TermeUpdateView(UpdateView, LoginRequiredMixin, SuccessMessageMixin):
    model = Terme
    fields = '__all__'
    success_message = "Le terme %(mot)s a bien été modifié."
    template_name = "glossaire/crud/terme_ajout.html"
    success_url = "/glossaire/"

class SourceCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
    model = Source
    fields = '__all__'
    success_message = "Source ajoutée au glossaire. Merci."
    template_name = "glossaire/crud/source_ajout.html"
    success_url = "/glossaire/"
