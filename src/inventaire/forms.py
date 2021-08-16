from django import forms
from .models import DocumentSite

class DocSiteForm(forms.ModelForm):
    class Meta:
        model = DocumentSite
        fields = ['doc', 'site',]
