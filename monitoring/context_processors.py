from .views import get_alerts_queryset

def alerts_context(request):
    alerts = get_alerts_queryset()
    count = len(alerts) if hasattr(alerts, '__len__') else alerts.count()
    return {
        'unread_alerts_count': count
    }
