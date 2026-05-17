from django.contrib import admin
from .models import Stitek, Seznam, Prvek

@admin.register(Stitek)
class StitekAdmin(admin.ModelAdmin):
    list_display = ('nazev', 'barva', 'specialni_vyznam', 'vlastnik')
    list_filter = ('vlastnik', 'specialni_vyznam')
    search_fields = ('nazev', 'specialni_vyznam')
    ordering = ('nazev',)

@admin.register(Prvek)
class PrvekAdmin(admin.ModelAdmin):
    list_display = ('nazev', 'vlastnik', 'smazano', 'archivovano', 'datum_vytvoreni')
    list_filter = ('smazano', 'archivovano', 'vlastnik', 'stitky')
    search_fields = ('nazev', 'obsah')
    filter_horizontal = ('stitky', 'souvisejici_prvky')
    readonly_fields = ('datum_vytvoreni', 'datum_upravy')
    date_hierarchy = 'datum_vytvoreni'
    ordering = ('-datum_vytvoreni',)

@admin.register(Seznam)
class SeznamAdmin(admin.ModelAdmin):
    list_display = ('nazev', 'vlastnik', 'velikostni_typ')
    list_filter = ('velikostni_typ', 'vlastnik')
    search_fields = ('nazev', 'popis')
    filter_horizontal = ('prvky', 'podseznamy', 'stitky_jako_polozky', 'stitky')
    ordering = ('nazev',)
