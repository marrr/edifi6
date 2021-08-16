# Generated by Django 3.2.5 on 2021-08-16 09:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventaire', '0002_delete_adressepostale'),
    ]

    operations = [
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified', models.DateTimeField(auto_now=True, null=True)),
                ('usage', models.PositiveSmallIntegerField(choices=[(1, 'Simple Adresse'), (2, 'Adresse de Site'), (3, 'Adresse de Domicile'), (4, 'Adresse de livraison énergie (EAN)'), (5, "Définie par l'usager")], default=1)),
                ('desc_autre_usage', models.CharField(blank=True, help_text='A quel usage servira cette Adresse', max_length=256, null=True)),
                ('nom_autre_usage', models.CharField(blank=True, help_text='Donner un nom à cet usage', max_length=124, null=True)),
                ('voirie', models.CharField(help_text='En toutes lettres. Les noms de rue ne doivent inclure AUCUNE \t\tautre note ou information, telle que les noms de la sous-commune, etc.', max_length=255, verbose_name='Voirie')),
                ('numero', models.CharField(blank=True, help_text='Si 2 séries de chiffres distincts, utiliser tiret (« - »)', max_length=21, null=True, verbose_name='Numéro')),
                ('boite', models.CharField(blank=True, max_length=7, null=True, verbose_name='boîte')),
                ('localite', models.CharField(blank=True, help_text='La localité, et non pas la commune.', max_length=124, null=True, verbose_name='Localité')),
                ('cp', models.CharField(blank=True, help_text='4 chiffres, pas d’initiale de pays,ni de code ISO', max_length=6, null=True, verbose_name='Code postal')),
                ('region', models.CharField(blank=True, choices=[('BE-VLG', 'Flandre'), ('BE-BRU', 'Bruxelles'), ('BE-WAL', 'Wallonie')], max_length=6, null=True, verbose_name='Région')),
                ('latitude', models.FloatField(default=0, editable=False)),
                ('longitude', models.FloatField(default=0, editable=False)),
                ('commune', models.CharField(blank=True, editable=False, max_length=100, null=True)),
                ('infomsg', models.CharField(blank=True, editable=False, max_length=275, null=True)),
                ('is_best', models.BooleanField(default=False, editable=False)),
                ('X', models.FloatField(default=0, editable=False)),
                ('Y', models.FloatField(default=0, editable=False)),
                ('composition', models.CharField(choices=[('C', 'COMPLEXE'), ('E', 'ELEMENTAIRE'), ('P', 'PARTIEL')], help_text="Déomposition de l'élément de structure spatiale", max_length=1, verbose_name='Composition')),
                ('service', models.CharField(choices=[('Service général des Infrastructures scolaires', (('DRBXL', 'Direction Régionale de Bruxelles'), ('DRBW', 'Direction Régionale du Brabant Wallon'), ('DRNO', 'Direction Régionale du Hainaut'), ('DRLG', 'Direction Régionale de Liège'), ('DRLX', 'Direction Régionale du Luxembourg'), ('DRNM', 'Direction Régionale de Namur'))), ('Service général du Patrimoine et de la Gestion immobilière', (('DICHA', 'Direction des Implantations culturelles et des Hôpitaux académique'), ('DISIPPJ', 'Direction des Implantations Sportives et des IPPJ'), ('DIAAJMJ', "Direction des Implantations administratives, de l'Aide à la Jeunesse et des Maisons de Justice"))), ('Service général des Infrastructures scolaires subventionnées', (('SubLiege', 'Service de Liège'), ('SubNam', 'Service de Namur'), ('SubNO', 'Service du Hainaut'), ('SubBrab', 'Service de Bruxelles et du Brabant Wallon'), ('SubLux', 'Service du Luxembourg')))], help_text='Le service au sein de la DGI.', max_length=10, verbose_name='Service Gestionnaire')),
                ('nom', models.CharField(blank=True, help_text="Si le site n'est pas nommé, il sera représenté par son Adiresse Postale", max_length=75, verbose_name='Nom usuel')),
                ('slug', models.SlugField(editable=False, max_length=255, unique=True)),
                ('edific', models.CharField(blank=True, help_text='n°EDIFIC, le cas échéant', max_length=7, null=True)),
                ('created_by', models.ForeignKey(blank=True, default=None, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventaire_site_created', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, default=None, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inventaire_site_modified', to=settings.AUTH_USER_MODEL)),
                ('tags', taggit.managers.TaggableManager(blank=True, help_text='Une liste de mots-clés séparés par une virgule, en minuscule', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Mots-clés')),
            ],
            options={
                'ordering': ('voirie',),
            },
        ),
    ]