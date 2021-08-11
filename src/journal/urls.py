from django.urls import path
from . import views

app_name = 'journal'

urlpatterns = [
	path('', views.index, name='index'),
	path('article/ajout/', views.ArticleCreateView.as_view(), name="nouvel-article"),
	path('article/<slug:slug>/', views.ArticleDetailView.as_view(), name="article-details"),
	path('article/<slug:slug>/edition/', views.ArticleUpdateView.as_view(), name="article-edition"),
	path('article/<slug:slug>/deletion/', views.ArticleDeleteView.as_view(), name="article-delete"),
]
