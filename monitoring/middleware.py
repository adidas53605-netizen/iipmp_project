from django.shortcuts import redirect
from django.urls import reverse
from .models import UserProfile

class ProfileSetupMiddleware:
    """
    Redirects authenticated users who haven't completed their initial profile setup
    to /profile/setup/. Exempts setup page, logout, static files, media, and admin.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path_info
            
            exempt_prefixes = [
                '/profile/setup',
                '/logout',
                '/login',
                '/admin-login',
                '/static',
                '/media',
                '/admin',
            ]

            if not any(path.startswith(prefix) for prefix in exempt_prefixes):
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                if not profile.profile_completed:
                    return redirect('profile_setup')

        return self.get_response(request)
