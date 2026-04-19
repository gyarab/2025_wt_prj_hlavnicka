from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Stitek(models.Model):
    nazev = models.CharField(max_length=100)
    barva = models.CharField(max_length=7)  # Hex kód barvy
    specialni_vyznam = models.CharField(max_length=255, null=True, blank=True)
    vlastnik = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.nazev
    
class Prvek(models.Model):
    nazev = models.CharField(max_length=225)
    obsah = models.TextField(null=True, blank=True)
    stitky = models.ManyToManyField(Stitek, blank=True)
    vlastnik = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    smazano = models.BooleanField(default=False)
    archivovano = models.BooleanField(default=False)
    datum_vytvoreni = models.DateTimeField(auto_now_add=True)
    datum_upravy = models.DateTimeField(auto_now=True)
    datum_zacatku = models.DateTimeField(null=True, blank=True)
    datum_konce = models.DateTimeField(null=True, blank=True)

    souvisejici_prvky = models.ManyToManyField('self', blank=True)

    def __str__(self):
        return f"{self.nazev}, ({self.vlastnik.username}){' [X]' if self.smazano else ''}"

class Seznam(models.Model):
    nazev = models.CharField(max_length=225)
    popis = models.TextField(null=True, blank=True)
    vlastnik = models.ForeignKey(User, on_delete=models.CASCADE)
    # seznam může obsahovat prvky, seznamy nebo štítky
    prvky = models.ManyToManyField(Prvek, blank=True, related_name='seznamy_prvku')
    podseznamy = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='nadseznamy')
    stitky_jako_polozky = models.ManyToManyField(Stitek, blank=True, related_name='seznamy_stitku_vseznamu')
    stitky = models.ManyToManyField(Stitek, blank=True, related_name='seznamy_stitku')

    velikostni_typ = models.CharField(max_length=20, choices=[('malý', 'Malý'), ('střední', 'Střední'), ('velký', 'Velký')], default='střední')

    def __str__(self):
        return self.nazev
