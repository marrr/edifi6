from django.urls import path
from . import views

app_name = 'inventaire'

urlpatterns = [
	path('', views.index, name='index'),
	path('annuaire/', views.annuaire, name='annuaire'),
	# RECHERCHE
	path('search/', views.SearchView.as_view(), name="recherche"),
	# ELEMENTS
	path('composants/', views.ComposantView.as_view(), name="composants"),
	# EXPORTATIONS
	path('sites/export/', views.export_sites, name="export-sites"),
	# SITE CRUD
	path('site/<slug:slug>/impression/', views.RapportPDFView.as_view(), name="site-print"),
	path('site/ajout/', views.SiteCreateView.as_view(), name="nouveau-site"),
	path('site/<slug:slug>/', views.SiteDetailView.as_view(), name="site-details"),
	path('sites/', views.SiteListView.as_view(), name="site-list"),
    path('site/<slug:slug>/modifications/', views.SiteUpdateView.as_view(), name="site-modif"),
    path('site/<slug:slug>/suppression/', views.SiteDeleteView.as_view(), name="site-delete"),
	# PARCELLE CRUD
	path('parcelle/ajout/', views.ParcelleCreateView.as_view(), name="nouvelle-parcelle"),
	path('parcelle/<slug:slug>/modifications/', views.ParcelleUpdateView.as_view(), name="parcelle-modif"),
	path('parcelle/<slug:slug>/suppressions/', views.ParcelleDeleteView.as_view(), name="parcelle-delete"),
	path('parcelles/', views.ParcelleListView.as_view(), name="parcelle-list"),
	path('parcelle/<slug:slug>/', views.ParcelleDetailView.as_view(), name="parcelle-details"),
	# BATIMENT CRUD
	path('batiments/', views.BatimentListView.as_view(), name="batiment-list"),
	path("batiment/ajout/", views.BatimentCreateView.as_view(), name="nouveau-batiment"),
	path("batiment/<slug:slug>/", views.BatimentDetailView.as_view(), name="batiment-details"),
	path("batiment/<slug:slug>/modifications/", views.BatimentUpdateView.as_view(), name="batiment-modif"),
	path("batiment/<slug:slug>/suppression/", views.BatimentDeleteView.as_view(), name="batiment-delete"),
	# NIVEAU CRUD
	path('niveaux/',views.NiveauListView.as_view(), name="niveaux-list"),
	path('niveau/ajout/', views.NiveauCreateView.as_view(), name="nouveau-niveau"),
	path('niveau/<int:pk>/',views.NiveauDetailView.as_view(), name="niveau-details"),
	path('niveau/<int:pk>/modifications/', views.NiveauUpdateView.as_view(), name="niveau-modif"),
	# MESURES SURFACE CRUD
	path('mesuredesurface/ajout/', views.MesureSurfaceCreateView.as_view(), name="nouvelle-mesuredesurface"),
	path("typedemesuredesurface/ajout/", views.TypeMesureSurfaceCreateView.as_view(), name="nouveau-typedemesuredesurface"),
	# MEMO CRUD
	path("memos/", views.MemoListView.as_view(), name="memo-list"),
	path("memo/ajout/", views.MemoCreateView.as_view(), name="nouveau-memo"),
	path("memo/<slug:slug>/", views.MemoDetailView.as_view(), name="memo-details"),
	path('memo/<slug:slug>/suppression/', views.MemoDeleteView.as_view(), name="memo-delete"),
	# RAPPORT
	path("rapports/", views.RapportListView.as_view(), name="rapport-list"),
	path('rapport/ajout/', views.RapportCreateView.as_view(), name="nouveau-rapport"),
	path('rapport/<int:pk>/modifications/', views.RapportUpdateView.as_view(), name="rapport-modif"),
	path("rapport/<int:pk>/suppression/", views.RapportDeleteView.as_view(), name="rapport-delete"),
	path("rapport/<int:pk>/", views.RapportDetailView.as_view(), name="rapport-details"),
	# AGENT CRUD
	path('agent/ajout/', views.AgentCreateView.as_view(), name="nouvel-agent"),
	path("agents/", views.AgentListView.as_view(), name="agent-list"),
	path('agent/<slug:slug>/', views.AgentDetailView.as_view(), name="agent-details"),
	path('agent/<slug:slug>/modifications/', views.AgentUpdateView.as_view(), name="agent-modif"),
	path("agent/<slug:slug>/suppression/", views.AgentDeleteView.as_view(), name="agent-delete"),
	# AGENTS DE SITE CRUD
	path('affectationagent/', views.AffectationAgentListView.as_view(), name="affectationagent-list"),
	path('affectationagent/ajout/', views.AffectationAgentCreateView.as_view(), name="nouvelle-affectationagent"),
	# OCCUPATION CRUD
	path('occupations/', views.OccupationListView.as_view(), name="occ-list"),
	path('occupation/ajout/', views.OccupationCreateView.as_view(), name="nouvelle-occupation"),
	# ORGANISATION CRUD
	path('organisation/ajout/', views.OrgaCreateView.as_view(), name="nouvelle-organisation"),
	path('organisation/<slug:slug>/modifications/', views.OrgaUpdateView.as_view(), name="org-modif"),
	path('organisation/<slug:slug>/suppression/', views.OrgaDeleteView.as_view(), name="org-delete"),
	path('organisation/<slug:slug>/', views.OrgaDetailView.as_view(), name="org-details"),
	path('organisations/', views.OrgaListView.as_view(), name="org-list"),
	# DOCUMENT CRUD
	path('document/ajout/', views.DocCreateView.as_view(), name="nouveau-doc"),
	path('documents/', views.DocListView.as_view(), name="doc-list"),
	# COMPTEURS OFFICIELS CRUD
	path('compteur_officiel/ajout/', views.CompteurOfficielCreateView.as_view(), name="nouveau-co"),
	path('compteur_officiel/<slug:slug>/modifications/', views.CompteurOfficielUpdateView.as_view(), name="co-modif"),
	path('compteur_officiel/<slug:slug>/suppression/', views.CompteurOfficielDeleteView.as_view(), name="co-delete"),
	path('compteur_officiel/<slug:slug>/', views.CompteurOfficielDetailView.as_view(), name="co-details"),
	path('compteurs_officiels/', views.CompteurOfficielListView.as_view(), name="co-list"),
	# RELEVE CRUD
	path('releve/ajout/', views.RlvCreateView.as_view(), name="nouveau-rlv"),
	path('releve/<int:pk>/modifications/', views.RlvUpdateView.as_view(), name="rlv-modif"),
	path('releve/<int:pk>/suppression/', views.RlvDeleteView.as_view(), name="rlv-delete"),
	path('releve/<int:pk>/', views.RlvDetailView.as_view(), name="rlv-details"),
	path('releves/', views.RlvListView.as_view(), name="rlv-list"),
]
