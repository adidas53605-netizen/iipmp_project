from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<str:project_id>/', views.project_detail, name='project_detail'),
    path('database/', views.database_manage, name='database_manage'),
    path('database/project/add/', views.project_create, name='project_create'),
    path('database/project/<str:project_id>/edit/', views.project_edit, name='project_edit'),
    path('database/project/<str:project_id>/delete/', views.project_delete, name='project_delete'),
    path('database/project/<str:project_id>/milestone/add/', views.milestone_create, name='milestone_create'),
    path('database/project/<str:project_id>/milestone/<int:milestone_id>/edit/', views.milestone_edit, name='milestone_edit'),
    path('analytics/', views.analytics, name='analytics'),
    path('budget/', views.budget_view, name='budget'),
    path('states/', views.states_view, name='states'),
    path('ministries/', views.ministries_view, name='ministries'),
    path('review/', views.review, name='review'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('help/', views.help_page, name='help'),
    path('database/import-csv/', views.csv_import, name='csv_import'),
    path('api/search/', views.search_api, name='search_api'),
    path('api/alerts/', views.api_alerts, name='api_alerts'),
    path('api/dashboard/', views.api_dashboard, name='api_dashboard'),
    path('dashboard/export/', views.export_dashboard_csv, name='export_dashboard_csv'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
