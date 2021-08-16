from django.contrib import admin
from .models import *

admin.site.register([
    Releve,
    Site,
    Parcelle,
    Batiment,
    Niveau,
    TypeMesureSurface,
    MesureSurface,
    Rapport,
    Memo,
    DocumentSite,
    Agent,
    AffectationAgent,
    Occupation,
    Organisation,
    CompteurOfficiel,
])