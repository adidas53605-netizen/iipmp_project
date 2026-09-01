from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('monitoring.urls')),
]

handler404 = 'monitoring.views.handler404'
handler500 = 'monitoring.views.handler500'
