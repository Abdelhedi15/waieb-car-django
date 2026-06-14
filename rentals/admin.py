from django.contrib import admin
from .models import Client, Reservation, Favori, IncidentVehicule

admin.site.register(Client)
admin.site.register(Reservation)
admin.site.register(Favori)

@admin.register(IncidentVehicule)
class IncidentVehiculeAdmin(admin.ModelAdmin):
    list_display  = ['vehicle', 'type_incident', 'gravite', 'zone', 'date_incident', 'repare', 'cout_reparation']
    list_filter   = ['type_incident', 'gravite', 'repare']
    search_fields = ['vehicle__immatriculation', 'vehicle__marque', 'description']
    date_hierarchy = 'date_incident'