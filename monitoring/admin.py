from django.contrib import admin
from .models import Project, Milestone, Alert, UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'role', 'ministry', 'state', 'profile_completed', 'created_at')
    list_filter = ('role', 'profile_completed', 'ministry', 'state')
    search_fields = ('user__username', 'user__email', 'full_name', 'employee_id')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('project_id', 'name', 'ministry', 'status', 'risk_level')
    list_filter = ('status', 'risk_level', 'ministry', 'state')
    search_fields = ('project_id', 'name', 'implementing_agency')

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'target_date', 'status')
    list_filter = ('status',)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'project', 'severity', 'created_at', 'is_read')
    list_filter = ('severity', 'alert_type', 'is_read')
