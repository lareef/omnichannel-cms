from django.contrib import admin
from .models import Role, Department, User, UserPreference  
from django.contrib.auth.admin import UserAdmin

admin.site.register(Role)
admin.site.register(Department)
#admin.site.register(User)
admin.site.register(UserPreference)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'role')
    list_filter = ('is_active', 'role', 'groups')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'department', 'is_active_employee')}),
    )
    actions = ['activate_users', 'deactivate_users']

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_users.short_description = "Deactivate selected users"
    
    
admin.site.register(User, CustomUserAdmin)

