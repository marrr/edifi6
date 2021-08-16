from .models import *
from inventaire.resources import SiteResource
from .forms import DocSiteForm
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.forms.widgets import CheckboxSelectMultiple
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView, UpdateView, DetailView, ListView, DeleteView, View, TemplateView
from django.db.models import When, Sum, Min, Count, Avg, Max, F, Q, ExpressionWrapper, DurationField, DateField, CharField, Case, Value
import random
from bootstrap_datepicker_plus import DateTimePickerInput

@login_required
def index(request):
	sites = Site.objects.all()
	total_site = sites.count()
	parcelles = Parcelle.objects.all()
	total_parcelle = parcelles.count()
	total_patris = parcelles.aggregate(Sum('patris'))['patris__sum']
	batiments = Batiment.objects.all()
	total_batiment = batiments.count()
	compt_off = CompteurOfficiel.objects.all()
	agents = Agent.objects.all()
	context = {
		'total_site':total_site,
		'sites':sites,
		'parcelles':parcelles,
		'total_parcelle':total_parcelle,
		'total_batiment':total_batiment,
		'total_patris':total_patris,
		'compt_off':compt_off,
		'agents':agents,
		}
	return render(request, 'inventaire/accueil.html', context)

@login_required
def annuaire(request):
	agents = list(Agent.objects.all())
	orgs = list(Organisation.objects.all())
#	agents_sample = random.sample(agents, 5)
#	orgs_sample = random.sample(orgs, 1)
	context = {
		'agents':agents,
		'orgs': orgs
		}
	return render(request, 'inventaire/annuaire.html', context)

class ComposantView(TemplateView):
	template_name = "inventaire/composants.html"

	def get_context_data(self,**kwargs):
		context = super().get_context_data(**kwargs)
		context['compteurs_officiels'] = CompteurOfficiel.objects.all()
		return context
########################################################## RECHERCHE MULTIFIELD
from django.db.models import Q
from django.apps import apps

class SearchView(LoginRequiredMixin, ListView):
	template_name = "inventaire/search.html"

	def get_context_data(self,**kwargs):
		context = super().get_context_data(**kwargs)
		rq = self.request.GET.get('q')
		context['terme_recherche'] = rq
		return context 

	def get_queryset(self,*args,**kwargs):
		excluded = ["Profile","TaggedItem","Tag",]
		modeles = [x for x in apps.get_models() if x.__name__ not in excluded]
		resultats = []
		rq = self.request.GET.get('q')
		for modele in modeles:
			fields = [x for x in modele._meta.fields if isinstance(x, CharField)]
			search_queries = [Q(**{x.name + "__icontains" : rq}) for x in fields]
			q_object = Q()
			for query in search_queries:
				q_object = q_object | query
			results = modele.objects.filter(q_object).distinct()
			if results:
				resultats.append({'nom':modele.__name__, 'resultats':results})
		return resultats
##################################################################### PRINT SITE
import io
from django.http import FileResponse
from reportlab.pdfgen import canvas

class RapportPDFView(View):

	def get(self,request,*args,**kwargs):
		# Create a file-like buffer to receive PDF data.
		buffer = io.BytesIO()
		# Create the PDF object, using the buffer as its "file."
		p = canvas.Canvas(buffer)
		site = request.headers["Referer"].split('/')[-2]
		qs = Site.objects.filter(slug=site)
		p.drawString(10, 10, f"{ qs }")
		# Close the PDF object cleanly, and we're done.
		p.showPage()
		p.save()
		# FileResponse sets the Content-Disposition header so that browsers
		# present the option to save the file.
		buffer.seek(0)
		return FileResponse(buffer, as_attachment=True, filename='hello.pdf')
######################################################################### EXPORT
def export_sites(request):
	if request.method == 'POST':
		file_format = request.POST['file-format']
		dir_op = request.POST['dir-op']
		reg = request.POST['regio']
		if reg == "Bruxelles":
			regio = "BE-BRU"
		elif reg == "Wallonie":
			regio = "BE-WAL"
		elif reg == "Flandre":
			regio = "BE-VLG"
		else:
			regio = None
		qs = Site.objects.filter(service=dir_op).filter(region=regio)
		sites = SiteResource()
		dataset = sites.export(qs)
		if file_format == 'CSV':
			response = HttpResponse(dataset.csv, content_type='text/csv')
			response['Content-Disposition'] = 'attachment; filename="exported_sites.csv"'
			return response
		elif file_format == 'JSON':
			response = HttpResponse(dataset.json, content_type='application/json')
			response['Content-Disposition'] = 'attachment; filename="exported_sites.json"'
			return response
		elif file_format == 'XLS':
			response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
			response['Content-Disposition'] = 'attachment; filename="exported_sites.xls"'
			return response

	return render(request, 'inventaire/rapports/export.html')
###################################################################### SITE CRUD
class SiteListView(LoginRequiredMixin, ListView):
	model = Site
	paginate_by = 10
	template_name="inventaire/crud/site/site_list.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		directions = ['dicha','disippj','diaajmj']
		for direction in directions:
			context[direction] = Site.objects.filter(service=direction)
		context['total'] = Site.objects.all().count()
		return context

class SiteDetailView(LoginRequiredMixin, DetailView):
	model = Site
	template_name="inventaire/crud/site/site_details.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["related_tags"] = self.object.tags.similar_objects()
		documents = DocumentSite.objects.filter(site_id=self.object)
		parcelles = Parcelle.objects.filter(site_id=self.object)
		energies = CompteurOfficiel.objects.filter(livraison_id=self.object)
		consos = Releve.objects.filter(compteur__in=energies)
		context["images"] = documents.filter(doc__contains='/images/')
		context["documents"] = documents.exclude(doc__contains='/images/')
		context['agents'] = AffectationAgent.objects.filter(site_id=self.object)
		context['occupants'] = Occupation.objects.filter(site=self.object)
		context['surface_cadastrale_totale'] = parcelles.aggregate(Sum('patris'))['patris__sum']
		context['energies'] = energies
		context['consos'] = consos.values('compteur__identifiant', 'compteur__fluide', 'debut_periode__year', 'compteur__slug')\
							.order_by('compteur__identifiant', 'compteur__fluide')\
							.annotate(c_annuel=Sum('quantite'))
		return context

class SiteCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = Site
	fields = ['nom','voirie','numero','boite','cp',
	'localite','region','tags', 'composition','service','edific']
	template_name="inventaire/crud/site/site_ajout.html"
	success_message = "Site ajouté à l'inventaire. Merci !"
	success_url = "/inventaire/site/{slug}/"

class SiteUpdateView(LoginRequiredMixin, UpdateView, SuccessMessageMixin):
	model = Site
	fields = ['nom','voirie','numero','boite','cp',
	'localite','region','tags', 'composition','service','edific']
	template_name="inventaire/crud/site/site_ajout.html"
	success_message = "%(nom)s a bien été modifié."

class SiteDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
	model = Site
	template_name="inventaire/crud/objet_a_effacer.html"
	success_url = reverse_lazy('inventaire:site-list')
################################################################## Parcelle CRUD
class ParcelleListView(LoginRequiredMixin, ListView):
	model = Parcelle
	paginate_by = 10
	template_name = "inventaire/crud/parcelle/parcelle_list.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['total'] = Parcelle.objects.all().count()
		return context

class ParcelleCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = Parcelle
	fields = '__all__'
	template_name = "inventaire/crud/parcelle/parcelle_ajout.html"
	success_url = reverse_lazy('inventaire:parcelle-list')

	def get(self,request,*args,**kwargs):
		slug_site = self.request.headers["Referer"].split('/')[-2]
		form = super().get_form()
		if slug_site not in ["parcelles","inventaire"]:
				initial_d = self.get_initial()
				initial_d['site'] = Site.objects.get(slug=slug_site)
				form.initial = initial_d
		return render(request, self.template_name,{'form':form})

	def post(self,request,*args,**kwargs):
		form = self.get_form()
		if form.is_valid():
			super().form_valid(form)
			return HttpResponseRedirect(self.get_success_url())
		self.object = None
		return self.form_invalid(form)

class ParcelleDetailView(LoginRequiredMixin, DetailView):
	model = Parcelle
	fields = '__all__'
	template_name = "inventaire/crud/parcelle/parcelle_details.html"

class ParcelleUpdateView(LoginRequiredMixin, UpdateView, SuccessMessageMixin):
	model = Parcelle
	fields = '__all__'
	template_name = "inventaire/crud/parcelle/parcelle_ajout.html"
	success_message = "La fiche a bien été modifiée."
	success_url = reverse_lazy('inventaire:parcelle-list')

class ParcelleDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
	model = Parcelle
	template_name="inventaire/crud/objet_a_effacer.html"
	success_url = reverse_lazy('inventaire:parcelle-list')

################################################################## Batiment CRUD
class BatimentListView(LoginRequiredMixin, ListView):
	model = Batiment
	paginate_by = 10
	template_name = "inventaire/crud/batiment/batiment_list.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['total'] = Batiment.objects.all().count()
		return context

class BatimentCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = Batiment
	fields = '__all__'
	template_name = "inventaire/crud/batiment/batiment_ajout.html"
	success_message = "Bâtiment ajouté à l'inventaire."

class BatimentDetailView(LoginRequiredMixin, DetailView):
	model = Batiment
	template_name = "inventaire/crud/batiment/batiment_details.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		niveaux = Niveau.objects.filter(batiment_id=self.object)
		context['niveaux'] = niveaux
		context['somme_surface_niveaux'] = niveaux.aggregate(Sum('niveaux__valeur'))['niveaux__valeur__sum']
		context['mes_bat'] = MesureSurface.objects.filter(batiment_id=self.object)
		return context

class BatimentUpdateView(LoginRequiredMixin, UpdateView, SuccessMessageMixin):
	model = Batiment
	fields = '__all__'
	template_name = "inventaire/crud/batiment/batiment_ajout.html"

class BatimentDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
	model = Batiment
	template_name="inventaire/crud/objet_a_effacer.html"
	success_url = reverse_lazy('inventaire:batiment-list')
#################################################################### Niveau CRUD
class NiveauListView(LoginRequiredMixin, ListView):
	model = Niveau
	template_name = "inventaire/crud/niveau/niveau_list.html"

class NiveauCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = Niveau
	fields = '__all__'
	template_name = "inventaire/crud/niveau/niveau_ajout.html"

class NiveauDetailView(LoginRequiredMixin, DetailView):
	model = Niveau
	template_name = "inventaire/crud/niveau/niveau_details.html"

class NiveauUpdateView(LoginRequiredMixin, UpdateView, SuccessMessageMixin):
	model = Niveau
	fields = '__all__'
	template_name = "inventaire/crud/niveau/niveau_ajout.html"
######################################################### Mesure de Surface CRUD
class MesureSurfaceCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = MesureSurface
	fields = '__all__'
	template_name = "inventaire/crud/mesuresurface/mesuresurface_ajout.html"

class TypeMesureSurfaceCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = TypeMesureSurface
	fields = '__all__'
	template_name = "inventaire/crud/mesuresurface/typesdemesuredesurface_ajout.html"
###################################################################### MEMO CRUD
class MemoDetailView(LoginRequiredMixin, DetailView):
	model = Memo
	template_name = "inventaire/crud/memo/memo_details.html"

class MemoListView(LoginRequiredMixin, ListView):
	model = Memo
	template_name = "inventaire/crud/memo/memo_list.html"

class MemoCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = Memo
	fields = '__all__'
	template_name = "inventaire/crud/memo/memo_ajout.html"
	success_message = "Merci pour votre message."
	success_url = "/inventaire/memo/{slug}/"

	def get(self,request,*args,**kwargs):
		slug_site = self.request.headers["Referer"].split('/')[-2]
		print (slug_site)
		form = super().get_form()
		if slug_site not in ["memos","inventaire"]:
				initial_d = self.get_initial()
				initial_d['site'] = Site.objects.get(slug=slug_site)
				form.initial = initial_d
		return render(request, self.template_name,{'form':form})

	def post(self,request,*args,**kwargs):
		form = self.get_form()
		if form.is_valid():
			super().form_valid(form)
			return HttpResponseRedirect(self.get_success_url())
		self.object = None
		return self.form_invalid(form)

class MemoDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
	model = Memo
	template_name = "inventaire/crud/objet_a_effacer.html"
	success_url = reverse_lazy('inventaire:memo-list')
################################################################### RAPPORT CRUD
class RapportListView(LoginRequiredMixin, ListView):
	model = Rapport
	template_name = "inventaire/rapports/accueil.html"
	success_message = "Ok"

class RapportCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = Rapport
	fields = "__all__"
	template_name = "inventaire/rapports/new_rep.html"
	success_message = "Rapport nouvellement créé"

	def get_form(self):
		form =super().get_form()
		form.fields['groupe'].widget = CheckboxSelectMultiple()
		return form

class RapportUpdateView(LoginRequiredMixin, UpdateView, SuccessMessageMixin):
	model = Rapport
	fields = "__all__"
	template_name = "inventaire/rapports/new_rep.html"

	def get_form(self):
		form =super().get_form()
		form.fields['groupe'].widget = CheckboxSelectMultiple()
		return form

class RapportDetailView(LoginRequiredMixin, DetailView):
	model = Rapport
	template_name = "inventaire/rapports/rep_details.html"

#    def get_context_data(self, **kwargs):
#        context = super().get_context_data(**kwargs)
#        return context
class RapportDeleteView(DeleteView, LoginRequiredMixin):
	model = Rapport
	template_name="inventaire/crud/objet_a_effacer.html"
	success_url = reverse_lazy('inventaire:rapport-list')
##################################################################### AGENT CRUD
class AgentListView(LoginRequiredMixin, ListView):
	model = Agent
	paginate_by = 5
	template_name = "inventaire/crud/agent/agent_list.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['total'] = Agent.objects.all().count()
		return context

class AgentDetailView(LoginRequiredMixin, DetailView):
	model = Agent
	template_name = "inventaire/crud/agent/agent_details.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['sites'] = AffectationAgent.objects.filter(agent_id=self.object)
		return context

class AgentCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = Agent
	fields = ['genre','nom','prenom','phone',"gsm","email","homepage"]
	template_name = "inventaire/crud/agent/agent_ajout.html"

class AgentUpdateView(LoginRequiredMixin, UpdateView, SuccessMessageMixin):
	model = Agent
	fields = ['genre','nom','prenom','phone',"gsm","email","homepage"]
	template_name = "inventaire/crud/agent/agent_ajout.html"
	success_message = "La fiche de %(label)s a bien été modifiée."

class AgentDeleteView(DeleteView, LoginRequiredMixin, SuccessMessageMixin):
	model = Agent
	template_name = "inventaire/crud/objet_a_effacer.html"
	success_url = reverse_lazy('inventaire:agent-list')
######################################################### Affectation de l'Agent
class AffectationAgentListView(LoginRequiredMixin, ListView):
	model = AffectationAgent
	template_name = "inventaire/crud/affectationagent/affectationagent_list.html"

class AffectationAgentCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = AffectationAgent
	fields = '__all__'
	template_name = "inventaire/crud/affectationagent/affectationagent_ajout.html"
	success_message = "%(agent)s a bien été modifié."

	def get(self,request,*args,**kwargs):
		slug = self.request.headers["Referer"].split('/')[-3]
		slug_detail = self.request.headers["Referer"].split('/')[-2]
		print (slug)
		form = super().get_form()
		initial_d = self.get_initial()
		if slug == "agent":
			initial_d['agent'] = Agent.objects.get(slug=slug_detail)
		elif slug == "site":
			initial_d['site'] = Site.objects.get(slug=slug_detail)
		form.initial = initial_d
		return render(request, self.template_name,{'form':form})

	def post(self,request,*args,**kwargs):
		form = self.get_form()
		if form.is_valid():
			super().form_valid(form)
			return HttpResponseRedirect(self.get_success_url())
		self.object = None
		return self.form_invalid(form)
################################################################ Occupation CRUD
class OccupationCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = Occupation
	fields = '__all__'
	success_message = "Organisation ajoutée au site. Merci !"
	template_name="inventaire/crud/occupation/occ_ajout.html"

	def get(self,request,*args,**kwargs):
		form = super().get_form()
		initial_d = self.get_initial()
		slug_site = self.request.headers["Referer"].split('/')[-2]
		initial_d['site'] = Site.objects.get(slug=slug_site)
		form.initial = initial_d
		return render(request, self.template_name,{'form':form})

	def post(self,request,*args,**kwargs):
		form = self.get_form()
		if form.is_valid():
			super().form_valid(form)
			return HttpResponseRedirect(self.get_success_url())
		self.object = None
		return self.form_invalid(form)

class OccupationListView(LoginRequiredMixin, ListView):
	model = Occupation
	template_name = "inventaire/crud/occupation/occ_list.html"
############################################################## Organisation CRUD
class OrgaCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = Organisation
	fields = '__all__'
	success_message = "Organisation ajoutée à l'inventaire. Merci !"
	template_name="inventaire/crud/organisation/org_ajout.html"

class OrgaDetailView(LoginRequiredMixin, DetailView):
	model = Organisation
	template_name = "inventaire/crud/organisation/org_details.html"

class OrgaListView(LoginRequiredMixin, ListView):
	model = Organisation
	template_name = "inventaire/crud/organisation/org_list.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['total'] = Organisation.objects.all().count()
		return context

class OrgaUpdateView(LoginRequiredMixin, UpdateView, SuccessMessageMixin):
	model = Organisation
	fields = '__all__'
	template_name = "inventaire/crud/organisation/org_ajout.html"
	success_message = "%(nom)s a bien été modifié."

class OrgaDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
	model = Organisation
	template_name = "inventaire/crud/objet_a_effacer.html"
	success_url = reverse_lazy('inventaire:org-list')
################################################################# Documents CRUD
class DocCreateView(LoginRequiredMixin, CreateView):
	model = DocumentSite
	form_class = DocSiteForm
	template_name = "inventaire/crud/document/doc_ajout.html"
	success_url = "/inventaire/documents/"

	def get(self,request,*args,**kwargs):
		slug_site = self.request.headers["Referer"].split('/')[-2]
		print (slug_site)
		form = super().get_form()
		if slug_site not in ["documents","inventaire"]:
				initial_d = self.get_initial()
				initial_d['site'] = Site.objects.get(slug=slug_site)
				form.initial = initial_d
		return render(request, self.template_name,{'form':form})

	def post(self,request,*args,**kwargs):
		form = self.get_form()
		if form.is_valid():
			super().form_valid(form)
			return HttpResponseRedirect(self.get_success_url())
		self.object = None
		return self.form_invalid(form)

class DocListView(LoginRequiredMixin, ListView):
	model = DocumentSite
	template_name = "inventaire/crud/document/doc_list.html"
####################################################### Compteurs Officiels CRUD
class CompteurOfficielCreateView(LoginRequiredMixin, CreateView):
	model = CompteurOfficiel
	fields = '__all__'
	template_name = "inventaire/crud/compteur_officiel/co_ajout.html"

#	def get(self,request,*args,**kwargs):
#		form = super().get_form()
#		initial_d = self.get_initial()
#		slug_site = self.request.headers["Referer"].split('/')[-2]
#		initial_d['livraison'] = Site.objects.get(slug=slug_site)
#		form.initial = initial_d
#		return render(request, self.template_name,{'form':form})

#	def post(self,request,*args,**kwargs):
#		form = self.get_form()
#		if form.is_valid():
#			super().form_valid(form)
#			return HttpResponseRedirect(self.get_success_url())
#		self.object = None
#		return self.form_invalid(form)

class CompteurOfficielListView(LoginRequiredMixin, ListView):
	model = CompteurOfficiel
	paginate_by = 10
	template_name = "inventaire/crud/compteur_officiel/co_list.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['total'] = CompteurOfficiel.objects.count()
		return context

class CompteurOfficielDetailView(LoginRequiredMixin, DetailView):
	model = CompteurOfficiel
	template_name = "inventaire/crud/compteur_officiel/co_details.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		consos = Releve.objects.filter(compteur_id=self.object)
		consos_stats = consos.aggregate(Min("debut_periode"), Max("fin_periode"), Sum('quantite'))
		nbr_rlv = consos.count
		context['stats'] = consos_stats
		context['nbr_rlv'] = nbr_rlv
		return context


class CompteurOfficielUpdateView(LoginRequiredMixin, UpdateView):
	model = CompteurOfficiel
	fields = '__all__'
	template_name = "inventaire/crud/compteur_officiel/co_ajout.html"

class CompteurOfficielDeleteView(DeleteView, LoginRequiredMixin):
	model = CompteurOfficiel
	template_name = "inventaire/crud/objet_a_effacer.html"
	success_url = reverse_lazy('inventaire:co-list')
################################################################### Relevés CRUD
class RlvCreateView(LoginRequiredMixin, CreateView, SuccessMessageMixin):
	model = Releve
	fields = '__all__'
	success_message = "Ajouté à l'inventaire. Merci !"
	template_name = "inventaire/crud/releve/rlv_ajout.html"

	def get_form(self):
		form = super().get_form()
		form.fields['debut_periode'].widget = DateTimePickerInput()
		form.fields['fin_periode'].widget = DateTimePickerInput()
		return form

class RlvDetailView(LoginRequiredMixin, DetailView, SuccessMessageMixin):
	model = Releve
	template_name = "inventaire/crud/releve/rlv_details.html"

class RlvListView(LoginRequiredMixin, ListView, SuccessMessageMixin):
	model = Releve
	paginate_by = 10
	template_name = "inventaire/crud/releve/rlv_list.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['total'] = Releve.objects.all().count()
		return context

class RlvUpdateView(LoginRequiredMixin, UpdateView, SuccessMessageMixin):
		model = Releve
		fields = '__all__'
		template_name = "inventaire/crud/releve/rlv_ajout.html"

class RlvDeleteView(LoginRequiredMixin, DeleteView, SuccessMessageMixin):
	model = Releve
	template_name = "inventaire/crud/objet_a_effacer.html"
	success_url = reverse_lazy('inventaire:rlv-list')