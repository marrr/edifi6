from django.urls import path
from . import views

app_name = "glossaire"

urlpatterns = [
	path('', views.TermeListView.as_view(), name='index'),
    path('terme/ajout/', views.TermeCreateView.as_view(), name="terme-ajout"),
    path('terme/<slug:slug>/', views.TermeDetailView.as_view(), name="terme-details"),
	path('terme/<slug:slug>/edition/', views.TermeUpdateView.as_view(), name="terme-modif"),
    path('source/ajout/', views.SourceCreateView.as_view(), name="source-ajout"),
]
