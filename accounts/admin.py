from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['username', 'nom', 'prenom', 'email', 'role', 'is_active']
    list_filter   = ['role', 'is_active']
    search_fields = ['username', 'nom', 'prenom', 'email']
    ordering      = ['username']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations Waieb', {'fields': ('nom', 'prenom', 'role')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations Waieb', {'fields': ('nom', 'prenom', 'role')}),
    )