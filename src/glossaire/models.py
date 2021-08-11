from journal.models import Cachet
from django.db import models
from django.urls import reverse
from django.shortcuts import render
from django.utils.text import slugify
from tinymce.models import HTMLField
from taggit.managers import TaggableManager

class Terme(Cachet):
    mot = models.CharField(max_length=150, verbose_name="Terme")
    desc = HTMLField(verbose_name="Définition(s)")
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    tags = TaggableManager(verbose_name="Mots-clés", blank=True, help_text="Une liste de mots-clés séparés par une virgule, en minuscule")

    def __str__(self):
        return self.mot

    def save(self,*args,**kwargs):
        self.slug = slugify(self)
        return super().save(*args,**kwargs)

    def get_absolute_url(self):
        return reverse('glossaire:terme-details', args=[self.slug])

    class Meta:
        ordering = ('mot',)

class Source(Cachet):
    label = models.CharField(max_length=100)
    lien = models.URLField(max_length=255)
    terme = models.ManyToManyField('Terme', related_name="references")

    def __str__(self):
        return self.label

    class Meta:
        ordering = ('label',)
