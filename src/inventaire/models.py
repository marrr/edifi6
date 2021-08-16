import requests
from pathlib import Path
import uuid
import os, environ
from django.db import models
from django.urls import reverse
from django.conf import settings
from geopy.geocoders import Here
from crum import get_current_user
from tinymce.models import HTMLField
from django.utils.text import slugify
from taggit.managers import TaggableManager
from django.core.exceptions import ValidationError
##################################
# FONCTIONS & VARIABLES DIVERSES #
##################################
def get_doc_filename(instance, filename):
	base_name = os.path.basename(filename)
	name, ext = os.path.splitext(base_name)
	extension = ext.split('.')[1]
	if extension in ['jpg','jpeg','png','svg','tiff','gif','psd','eps','ai','bmp']:
		dossier = 'images'
	elif extension == 'dwg':
		dossier = 'plan_autocad'
	else:
		dossier = extension
	return "docs/"+str(instance.site.pk)+"/"+dossier+'/'+filename

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(env_file=str(BASE_DIR / ".env"))
######################
# CLASSES ABSTRAITES #
######################
class Cachet(models.Model):
	'''Tous les objets héritent de cette classe pour que, lorsqu'un objet est
	manipulé, il reçoit un 'stamp' indiquant par qui et quand l'objet a été
	créé/modifié.
	Utilise la fonction get_current_user du package django-crum.
	IFC4 : Resource definition data schemas >> IfcUtilityResource >> IfcOwnerHistory
	'''
	created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
	created_by = models.ForeignKey('auth.User', blank=True, null=True, editable=False,
	on_delete=models.CASCADE, default=None, related_name='%(app_label)s_%(class)s_created')
	modified = models.DateTimeField(auto_now=True, null=True, blank=True)
	modified_by = models.ForeignKey('auth.User', blank=True, null=True, editable=False,
	on_delete=models.CASCADE, default=None, related_name='%(app_label)s_%(class)s_modified')

	def save(self, *args, **kwargs):
		user = get_current_user()
		if user and not user.pk:
			user = None
		if not self.pk:
			self.created_by = user
		self.modified_by = user
		return super(Cachet, self).save(*args, **kwargs)

	class Meta:
		abstract = True

class CompositionElement(models.Model):
	"""Cette classe reprend les différentes compositions possibles des éléments
	de la structure spatiale. Et donc les classes Sites, Bâtiments, Niveaux et
	Locaux en héritent.
	Un élément peut être :
	- COMPLEXE : l'élément fait partie d'un groupe ou d'une aggrégation d'
	éléments similaires
	- ELEMENT : l'élément en tant que tel, non divisé
	- PARTIAL : partie ou sous élément
	IFC4 : Core data schemas >> IfcProductExtension >> IfcElementCompositionEnum
	"""
	COMPOSITION = (
		('C', 'COMPLEXE'),
		('E', 'ELEMENTAIRE'),
		('P', 'PARTIEL')
	)
	composition = models.CharField(max_length=1, choices=COMPOSITION,
	verbose_name="Composition", help_text="Déomposition de l'élément de structure spatiale")

	class Meta:
		abstract = True

class ServiceGestionnaire(models.Model):
	"""Organigramme de la DGI."""
	SERVICES = [
		("Service général des Infrastructures scolaires", (
				('DRBXL', 'Direction Régionale de Bruxelles'),
				('DRBW', 'Direction Régionale du Brabant Wallon'),
				('DRNO', 'Direction Régionale du Hainaut'),
				('DRLG', 'Direction Régionale de Liège'),
				('DRLX', 'Direction Régionale du Luxembourg'),
				('DRNM', 'Direction Régionale de Namur'),
			)
		),
		('Service général du Patrimoine et de la Gestion immobilière', (
				('DICHA', 'Direction des Implantations culturelles et des Hôpitaux académique'),
				('DISIPPJ', 'Direction des Implantations Sportives et des IPPJ'),
				('DIAAJMJ', "Direction des Implantations administratives, de l'Aide à la Jeunesse et des Maisons de Justice"),
			)
		),
		("Service général des Infrastructures scolaires subventionnées", (
				('SubLiege','Service de Liège'),
				('SubNam', 'Service de Namur'),
				('SubNO', 'Service du Hainaut'),
				('SubBrab', 'Service de Bruxelles et du Brabant Wallon'),
				('SubLux', 'Service du Luxembourg'),
			)
		)
	]

	service = models.CharField(max_length=10, choices=SERVICES,
	verbose_name="Service Gestionnaire", help_text="Le service au sein de la DGI.")

	class Meta:
		abstract = True

class AdressePostale(models.Model):
	# Champs à compléter par l'utilisateur (tous requis, sauf numero)
	voirie = models.CharField(max_length=255, verbose_name="Voirie", blank=True, null=True,
	help_text="En toutes lettres. Les noms de rue ne doivent inclure AUCUNE autre note ou information, telle que les noms de la sous-commune, etc.")
	numero = models.CharField(max_length=21, verbose_name="Numéro",
	help_text="Si 2 séries de chiffres distincts, utiliser tiret (« - »)", blank=True, null=True)
	boite = models.CharField(max_length=7, blank=True, null=True, verbose_name="boîte")
	localite = models.CharField(max_length=124, verbose_name="Localité",
	help_text="La localité, et non pas la commune.", blank=True, null=True)
	cp = models.CharField(max_length=6, verbose_name="Code postal",
	help_text="4 chiffres, pas d’initiale de pays,ni de code ISO", blank=True, null=True)
	REGION = (
		('BE-VLG','Flandre'),
		('BE-BRU','Bruxelles'),
		('BE-WAL','Wallonie')
	)
	region = models.CharField(max_length=6, choices=REGION, verbose_name="Région", blank=True, null=True)
	# Coordonnées WSG84
	latitude = models.FloatField(editable=False, default=0)
	longitude = models.FloatField(editable=False, default=0)
	# Champs complétés automatiquement (editable=False)
	commune = models.CharField(max_length=100, editable=False, blank=True, null=True)
	infomsg = models.CharField(max_length=275, editable=False, blank=True, null=True)
	is_best = models.BooleanField(editable=False, default=False)
	# Coordonnées Belge 1972 / Belgian Lambert 72
	X = models.FloatField(editable=False, default=0)
	Y = models.FloatField(editable=False, default=0)

	def coordonnees_adresse(self):
		''' Définition des latitude et longitude de l'Adresse.'''
		geoloc = Here(apikey=env('HERE_APIKEY'))
		try:
			loc = geoloc.geocode(self.voirie+', '+self.numero+', '+\
		self.localite).raw['Location']['NavigationPosition'][0]
			return (loc['Latitude'], loc['Longitude'])
		except:
			return (0,0)

	def check_if_is_best(self):
		url = "http://geoservices.wallonie.be/geolocalisation/rest/getPositionBySmartGeocoding/"
		adresse = str(self.cp)+'/'+self.localite+'/'+self.voirie+'/'+str(self.numero)
		try:
			r = requests.get(url+adresse).json()
			self.infomsg = r['infoMsg']
			if not r['infoMsg'] and not r['errorMsg'] and r['errorCode'] == 0:
				self.is_best = True
			else:
				self.is_best = False
			return r['x'], r['y'], r['rue']['commune']
		except requests.exceptions.RequestException as e:
			self.infomsg = str(e)
			return (0,0,"")

	def __str__(self):
		return self.voirie+', '+str(self.numero)+' - '+str(self.cp)+' '+self.localite

	def save(self, *args,**kwargs):
		self.slug = slugify(self)
		if self.region != "BE-VLG":
			try:
				self.X, self.Y, self.commune = self.check_if_is_best()
			except:
				self.X, self.Y, self.commune = (0,0,"")
		self.latitude, self.longitude = self.coordonnees_adresse()
		return super().save(*args,**kwargs)

	class Meta:
		abstract = True

class AdresseTelecom(models.Model):
	'''Coordonnées de contact d'une personne et/ou d'une organisation.
	Au moins une coordonnée doit être remplie.
	Procédure de validation à écrire.
	IFC4 : Resource definition data schemas >> IfcActorResource >> IfcTelecomAddress
	'''
	phone = models.CharField(max_length=15, blank=True, null=True)
	gsm = models.CharField(max_length=15, blank=True, null=True)
	email = models.EmailField(blank=True, null=True)
	homepage = models.URLField(blank=True, null=True)

	def clean(self):
		if not (self.phone or self.gsm or self.email or self.homepage):
			raise ValidationError("Au moins une coordonnée doit être indiquée.")

	class Meta:
		abstract = True

class Personne(models.Model):
	'''Cette classe représente un être humain.
	IFC4 : Resource definition data schemas >> IfcActorResource >> IfcPerson
	'''
	GENRE = (
	('M','Monsieur'),
	('F','Madame'),
	('X','Non précisé')
	)
	genre = models.CharField(max_length=1, choices=GENRE)
	nom = models.CharField(max_length=225)
	prenom = models.CharField(max_length=124)

	def __str__(self):
		return self.prenom+' '+self.nom

	class Meta:
		abstract = True
		ordering = ('nom',)
#####################
# CLASSES PARTAGEES #
#####################
class Organisation(Cachet, AdresseTelecom):
	nom = models.CharField(max_length=255, help_text="Nom complet de l'Organisation")
	slug = models.SlugField(max_length=255, unique=True, editable=False)
	bce_ne = models.CharField(max_length=10, help_text="Dix chiffres, sans les points",
	blank=True, verbose_name="Numéro BCE")
	fase = models.PositiveIntegerField(help_text="n°FASE, si établissement scolaire", blank=True, null=True)

	def __str__(self):
	   return self.nom.upper()

	def save(self,*args,**kwargs):
		self.slug = slugify(self)
		return super().save(*args,**kwargs)

	def get_absolute_url(self):
		return reverse('inventaire:org-details', args=[self.slug])

class Occupation(Cachet):
	nom = models.CharField(max_length=255, null=True, blank=True, verbose_name="Nom donné à l' occupation")
	orga = models.ForeignKey('Organisation', on_delete=models.CASCADE,
	related_name="occupants", verbose_name="Occupant", null=True)
	site = models.ForeignKey('Site', on_delete=models.CASCADE, related_name="occupations",
	verbose_name="Site d'implantation")
	bce_ue = models.CharField(max_length=10, help_text="Dix chiffres, sans les points",
	blank=True, verbose_name="Numéro d'établissement BCE")

	def __str__(self):
		if not self.nom:
			return str(self.site)
		else:
			return self.nom

	def get_absolute_url(self):
		return reverse('org-list')

class Agent(Personne, AdresseTelecom):
	'''Un agent est une personne qui travaille au sein de la Direction Générale
	des Infrastructures du Secrétariat Général du Ministère de la Fédération
	Wallonie Bruxelles.
	IFC4 : NONE'''
	slug = models.SlugField(max_length=255, unique=True, editable=False)
	site = models.ManyToManyField('Site', through="AffectationAgent")

	class Meta:
		ordering = ('nom',)

	def __str__(self):
		return self.prenom+' '+self.nom

	def save(self,*args,**kwargs):
		self.slug = slugify(self)
		return super().save(*args,**kwargs)

	def get_absolute_url(self):
		return reverse('inventaire:agent-details', args=[self.slug])

class AffectationAgent(models.Model):
	agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
	site = models.ForeignKey('Site', on_delete=models.CASCADE)
	fonction = models.CharField(max_length=124)

	def __str__(self):
		return str(self.agent)+', '+self.fonction+' à '+str(self.site)

	def get_absolute_url(self):
		return reverse('inventaire:agent-details', args=[self.agent.slug])

	class Meta:
		verbose_name = "Affectation de l'Agent"
		verbose_name_plural = "Affectations de l'Agent"
		constraints = [
			models.UniqueConstraint(fields=['agent','site'], name="affectation_unique")
		]

class TypeMesureSurface(models.Model):
	nom = models.CharField(max_length=124, help_text="Nom complet")
	desc = models.CharField(max_length=248, help_text="Courte description", blank=True)
	acronyme = models.CharField(max_length=64, blank=True)

	def __str__(self):
		return self.nom

	class Meta:
		ordering = ('nom',)

class MesureSurface(Cachet):
	'''
	Une mesure de superficie est la valeur de l'étendue d'une surface. Elle est
	exprimée en m² et s'applique uniquement aux bâtiments et/ou aux niveaux et/ou
	aux locaux. En effet, seuls ces éléments sont réellement mesurés.
	La superficie d'un site est calculée (par aggrégation des éléments qui le
	composent) ; et la superficie d'un terrain est fournie par une Source Authentique (l'AGDP).
	'''
	valeur = models.FloatField(help_text="Valeur en m²")
	type = models.ForeignKey('TypeMesureSurface', on_delete=models.CASCADE, related_name="typologie")
	batiment = models.ForeignKey('Batiment', on_delete=models.CASCADE,
	related_name="batiments", blank=True, null=True)
	niveau = models.ForeignKey('Niveau', on_delete=models.CASCADE,
	related_name="niveaux", blank=True, null=True)

	def get_absolute_url(self):
		return reverse('inventaire:batiment-details', args=[self.batiment.slug])

	def __str__(self):
		if self.batiment:
			return "Mesure de surface du bâtiment "+str(self.batiment)
		elif self.niveau:
			return "Mesure de surface du niveau "+str(self.niveau)

	def clean(self):
		if self.niveau and self.batiment:
			raise ValidationError("On mesure soit le bâtiment soit un de ces niveaux, pas les deux en même temps.")

	class Meta:
		verbose_name_plural = "Mesures de surface"

class Rapport(Cachet):
	'''Un Rapport est un regroupement de site sur lequel est appliqué :
		- des opérations CRUD
		- des requêtes spécifiques
		- des visualisations
		- des exports (pdf, csv, xls)
	'''
	titre = models.CharField(max_length=100, help_text="Titre court et explicite")
	description = models.CharField(max_length=200, help_text="Courte description")
	contenu = HTMLField()
	groupe = models.ManyToManyField('Site',verbose_name="Sites d'intervention", related_name="elements")

	def __str__(self):
		return self.titre

	def get_absolute_url(self):
		return reverse('inventaire:rapport-details', args=[self.pk])

class DocumentSite(Cachet):
	site = models.ForeignKey('Site', default=None, on_delete=models.CASCADE)
	doc = models.FileField(upload_to=get_doc_filename, max_length=255, verbose_name="Document")

	def __str__(self):
		return str(self.doc).split('/')[-1]
###################
# CLASSES ENERGIE #
###################
class CompteurOfficiel(Cachet, AdressePostale):
	'''Un compteur d’énergie est un dispositif qui permet d’effectuer le comptage
	de l’énergie consommée ou injectée sur le réseau. On peut établir une
	classification des compteurs en fonction :
		- du type de fluide : électricité, gaz, eau, mazout,
		- des plages tarifaires proposées : mono-horaires, bi-horaires ou exclusif nuit,
		- la fréquence des relevés : annuel (YMR), mensuel (MMR), en continu (AMR),
		- de la technologie utilisée : électromécanique (les compteurs classiques), électronique ou intelligent,
		- de la direction du courant mesuré (unidirectionnel ou bidirectionnelle).
	Un compteur peut être soit un compteur officiel, soit un compteur
	de passage/sous-comptage/propre.
	Le compteur officiel est le compteur installé par le distributeur d'énergie.'''
	class Fluide(models.TextChoices):
		ELECTRICITE = 'E', 'Electricité'
		GAZ = 'G', 'Gaz'
		MAZOUT = 'M', 'Mazout'
		EAU = 'O', "Eau"
	fluide = models.CharField(max_length= 1, choices=Fluide.choices)
	class Tarif(models.IntegerChoices):
		MONO = 1, 'Mono-horaire'
		BI = 2, 'Bi-horaire'
		NUIT = 3, 'Exclusif Nuit'
	tarif = models.IntegerField(choices=Tarif.choices, default=1)
	class PeriodeReleve(models.TextChoices):
		YMR = 'YMR', 'Annuel'
		MMR = 'MMR', 'Mensuel'
		AMR = 'AMR', "Continu"
	releve = models.CharField(max_length=3, choices=PeriodeReleve.choices)
	class Debit(models.TextChoices):
		HT = "HT","Haute tension"
		BT = "BT","Basse tension"
		HP = "HP","Haute pression"
		BP = "BP","Basse pression"
	debit = models.CharField(max_length=2, choices=Debit.choices, blank=True, null=True)
	identifiant = models.CharField(max_length=25, unique=True)
	class Grds(models.TextChoices):
		ORES = ("ORS","ORES")
		RESA = ("RS","RESA")
		SIBELGA = ("SBLG","SIBELGA")
		VIVAQUA = ("VVQ",'VIVAQUA')
		AIEG = ('AIEG','AIEG')
		AIESH = ('AIESH', 'AIESH')
		FLUVIUS = ('FLVS','FLUVIUS')
		REW = ('REW','REW')
		SIBELGAS = ('SBLGS','SIBELGAS')
		SWDWE = ("SWD",'SWDwE')
	grd = models.CharField(max_length=10, choices=Grds.choices, blank=True, null=True)
	slug = models.SlugField(max_length=120, editable=False)
	livraison = models.ForeignKey('Site', on_delete=models.CASCADE, related_name="site", blank=True, null=True)

	def __str__(self):
		return self.identifiant

	def save(self,*args,**kwargs):
		self.slug = slugify(self.identifiant)
		return super().save(*args,**kwargs)

	def get_absolute_url(self):
		return reverse('inventaire:co-details', args=[self.slug])

	class Meta:
		verbose_name_plural = 'Compteurs Officiels'

class Releve(Cachet):
	compteur = models.ForeignKey(CompteurOfficiel, on_delete=models.CASCADE, related_name="releves")
	debut_periode = models.DateTimeField()
	fin_periode = models.DateTimeField()
	TARIF = [
		('Lo','Low'),
		('Hi','High'),
		('Th','Total Hours'),
	]
	quantite = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Quantité consommée", null=True,\
		help_text="En litre si c'est du mazout ou de l'eau, en kWh sinon")
	tarif = models.CharField(max_length=3, choices=TARIF)
#	slug = models.SlugField(max_length=120, null=False, unique=True, editable=False, default="")

#	def save(self,*args,**kwargs):
#		#PCS (Pouvoir Calorifique Supérieur) = 10.641
#		PCS = decimal.Decimal(10.641)
#		ref_str = str(self.ref.idean)
#		if ref_str.startswith('M_'):
#			self.quantite = self.quantite*PCS

	def get_absolute_url(self):
		return reverse('inventaire:rlv-details', args=[self.pk])

	def __str__(self):
		return str(self.compteur.identifiant)+' | '+str(self.fin_periode)
######################
# STRUCTURE SPATIALE #
######################
class Site(Cachet, AdressePostale, CompositionElement, ServiceGestionnaire):
	nom = models.CharField(max_length=75, verbose_name="Nom usuel", blank=True,
	help_text="Si le site n'est pas nommé, il sera représenté par son Adiresse Postale")
	tags = TaggableManager(verbose_name="Mots-clés", blank=True,
	help_text="Une liste de mots-clés séparés par une virgule, en minuscule")
	slug = models.SlugField(max_length=255, unique=True, editable=False)
	edific = models.CharField(max_length=7, help_text="n°EDIFIC, le cas échéant", blank=True,
	null=True)

	def __str__(self):
		if self.nom:
			return self.nom+' ['+self.voirie+', '+str(self.numero)+' - '+str(self.cp)+' '+self.localite+']'
		else:
			return self.voirie+', '+str(self.numero)+' - '+str(self.cp)+' '+self.localite

	def save(self, *args,**kwargs):
		self.slug = slugify(self)
		return super().save(*args,**kwargs)

	def get_absolute_url(self):
		return reverse('inventaire:site-details', args=[self.slug])

	class Meta:
		ordering = ('voirie',)

class Parcelle(Cachet):
	capakey = models.CharField(max_length=17, blank=True, null=True, verbose_name="CaPaKey",
	help_text="Le CaPaKey se compose toujours de 17 caractères, '/' compris.")
	patris = models.FloatField(blank=True, null=True, verbose_name="Contenance PATRIS (m²)",
	help_text="Superficie de la parcelle, comme indiquée dans la documentation patrimoniale.")
	nature = models.CharField(max_length=50, verbose_name="Nature", blank=True, null=True,
	help_text="Nature cadastrale de la parcelle concernée")
	site = models.ForeignKey('Site', on_delete=models.CASCADE,
	null=False, blank=False, related_name = "parcelles", verbose_name="Site")
	slug = models.SlugField(max_length=255, unique=True, editable=False)
	# matrice cadasstrale, champs non editables
	division = models.CharField(max_length=5, editable=False, default="11111")
	section = models.CharField(max_length=1, editable=False, default="A")
	radical = models.CharField(max_length=4, editable=False, default="2222")
	bis = models.CharField(max_length=2, editable=False, default="33")
	exposant = models.CharField(max_length=1, editable=False, default="A")
	puissance = models.CharField(max_length=3, editable=False, default="444")
	# Meme si le droit de propriété porte sur la parcelle cadastrale patrimoine,
	# on va attacher ce droit à la parcelle cadastrale plan. Charge à la DGBF
	DROIT = (
		('P','Propriété'),
		('L','Location'),
		('E','Emphytéose'),
		('SPABS',"SPABS"),
		('CP','CoPropriété'),
		('CS','CoSuperficaire'),
		('MD','Mise à Disposition'),
		('I','Inconnue')
	)
	droit = models.CharField(max_length=6, choices=DROIT, verbose_name="Situation patrimoniale")

	def __str__(self):
		return self.capakey+' : '+ str(self.site)

	def matriceCadastrale(self):
		cle = self.capakey
		self.division = cle[:5]
		self.section = cle[5]
		self.radical = cle[6:10]
		self.bis = cle[11:13]
		self.exposant = cle[13]
		self.puissance = cle[-3:]

	def save(self,*args,**kwargs):
		self.slug = slugify(self.capakey)
		self.matriceCadastrale()
		return super().save(*args,**kwargs)

	def get_absolute_url(self):
		return reverse('inventaire:parcelle-details', args=[self.slug])

	class Meta:
		ordering = ('site','capakey')
		constraints = [
			models.UniqueConstraint(fields=['capakey',], name="capakey_unique")
		]

class Batiment(Cachet, CompositionElement):
	"""
	La nomenclature des ouvrages de construction (CC) subdivise les
	constructions en "Bâtiments" et "Ouvrages de génie civil".
	Une CONSTRUCTION est une structure en contact avec le sol composée de
	matériaux de construction et des composants et/ou pour laquelle des travaux
	de construction sont réalisés.
	Un BATIMENT est un ouvrage de construction couvert pouvant être utilisés
	séparemment, conçu pour des besoins permanents, pouvant accueillir des personnes
	et adaptés à la protection de personnes, d'animaux ou d'objets.
	Un OUVRAGE DE GENIE CIVIL un ouvrage de construction non classé en bâtiment:
	chemins de fer, routes, terrains de sport, etc.
	Un bâtiment cadastral est un bâtiment dont l'AGDP (via la commune,
	le citoyen, la visite sur site,...) a établi qu'il a été mis en service.
	Un bâtiment a été mis en service dès le moment où il est utilisé en
	fonction de sa destination. Une utilisation à des fins autres que celles
	pour lesquelles le bâtiment a été construit peut également être considérée
	comme une mise en service, à condition que l'utilisation soit continue.
	Ce sont les Régions qui tiennent à jour le cadastre des bâtiments. La Wallonie
	accuse un retard relatif comparé à Bruxelles : la nomenclature wallonne n'est,
	à ma connaissance, pas encore fixée (v. PICC)
	Déf. IFC4 : A building represents a structure that provides shelter for its
	occupants or contents and stands in one place. The building is also used to
	provide a basic element within the spatial structure hierarchy for the
	components of a building project (together with site, storey, and space).
	A building is (if specified) associated to a site. A building may span over
	several connected or disconnected buildings. Therefore building complex
	provides for a collection of buildings included in a site. A building can
	also be decomposed in (vertical) parts, where each part defines a building section.
	Source Authentique : Pour Bruxelles, UrbIS-Adm est une carte numérique à
	caractère administratif et thématique. UrbIS-Adm contient des données
	géographiques et des données attributaires.
	IFC4 : Core data schemas >> IfcProductExtension >> IfcBuilding
	"""
	id_regional = models.CharField(max_length=175, help_text="Numéro de séquence unique fournie par les Régions")
	nom = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nom usuel")
	desc = models.CharField(max_length=255, blank=True, null=True,
	help_text="Courte description du bâtiment")
	shape_area = models.FloatField(blank=True, null=True, help_text="Superficie graphique du bâtiment, exprimée en m², fournie par l'ADGP")
	parcel = models.ForeignKey(Parcelle, on_delete=models.CASCADE, related_name="constructions",
	help_text="Sélectionner le terrain sur lequel se trouve le bâtiment")
	slug = models.SlugField(max_length=255, blank=True, unique=True, editable=False)
	nbr_niveau = models.PositiveSmallIntegerField(help_text="Sous-sol compris", blank=True, null=False, default=1)
	annee_cstr = models.PositiveSmallIntegerField(default=1976, blank=True, null=False, verbose_name="Année de construction")

	class Meta:
		ordering = ('parcel__site__voirie',)

	def __str__(self):
		if self.nom:
			return self.nom+' - '+str(self.parcel.site)
		else:
			return self.id_regional+' - '+str(self.parcel.site)

	def save(self, *args, **kwargs):
		self.slug = slugify(self)
		return super().save(*args,**kwargs)

	def get_absolute_url(self):
		return reverse('inventaire:batiment-details', args=[self.slug])

class Niveau(Cachet, CompositionElement):
	'''The building storey has an elevation and typically represents a (nearly)
	horizontal aggregation of spaces that are vertically bound. A storey is
	(if specified) associated to a building. A storey may span over several
	connected storeys. Therefore storey complex provides for a collection of storeys
	included in a building. A storey can also be decomposed in (horizontical)
	parts, where each part defines a partial storey.
	Niveau n'équivaut pas à étage (le 1er étage est en fait le 2ème niveau)
	IFC4 : Core data schemas >> IfcProductExtension >> IfcBuildingStorey
	'''
	nom = models.CharField(max_length=215, verbose_name="Nom usuel")
	desc = models.CharField(max_length=200)
	batiment = models.ForeignKey(Batiment, on_delete=models.CASCADE, related_name="niveaux")

	class Meta:
		verbose_name_plural = "Niveaux"

	def __str__(self):
		return "Niveau "+self.nom+" de "+str(self.batiment)

class Memo(Cachet):
	'''Un mémo est un commentaire, une remarque ou n'importe quelle information
	non structurée que l'utilisateur veut ajouter à un Site et/ou à l'un des
	éléments qui le composent.
	IFC4 : Core data schemas >> IfcProductExtension >> IfcAnnotation
	'''
	SUJETS = (
		('S','Site proprement dit'),
		('C', 'Construction'),
		('T', 'Terrain'),
		('E', 'Point de Fourniture Energétique'),
		('R', 'Relevé'),
		('F', 'Facture'),
		('O', 'Occupant'),
		('P', 'Personne'),
		('A', 'Autre'),
	)
	contenu = HTMLField(verbose_name="Memorandum")
	sujet = models.CharField(max_length=1, choices=SUJETS, verbose_name="Element du site concerné", default="S")
	site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="notes", verbose_name="Site objet du memo", null=True)
	slug = models.SlugField(max_length=255, unique=True, editable=False)

	class Meta:
		ordering = ('created',)

	def save(self,*args,**kwargs):
		self.slug = slugify(str(self.contenu)[:42])
		return super().save(*args,**kwargs)

	def __str__(self):
		return "Auteur : "+str(self.created_by)+" | Sujet:"+self.get_sujet_display()+" | Site : "+str(self.site)

	def get_absolute_url(self):
		return reverse('inventaire:memo-details', args=[self.slug])

