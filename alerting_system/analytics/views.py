from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from alerts.models import Alert, UserAlertPreference, NotificationDelivery

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_dashboard(request):
    """Get analytics data for the dashboard"""
    
    # Basic metrics
    total_alerts = Alert.objects.count()
    active_alerts = Alert.objects.filter(
        is_active=True,
        expiry_time__gt=timezone.now()
    ).count()
    
    # Delivery metrics
    total_deliveries = NotificationDelivery.objects.count()
    successful_deliveries = NotificationDelivery.objects.filter(
        status='SENT'
    ).count()
    
    # Read metrics
    total_preferences = UserAlertPreference.objects.count()
    read_count = UserAlertPreference.objects.filter(
        status='READ'
    ).count()
    snoozed_count = UserAlertPreference.objects.filter(
        status='SNOOZED'
    ).count()
    
    # Severity breakdown
    severity_breakdown = Alert.objects.values('severity').annotate(
        count=Count('id')
    )
    
    # Alert performance (top alerts by engagement)
    alert_performance = Alert.objects.annotate(
        total_sent=Count('notificationdelivery'),
        total_read=Count('useralertpreference', filter=Q(useralertpreference__status='READ')),
        total_snoozed=Count('useralertpreference', filter=Q(useralertpreference__status='SNOOZED'))
    ).order_by('-total_sent')[:10]
    
    alert_performance_data = []
    for alert in alert_performance:
        alert_performance_data.append({
            'id': alert.id,
            'title': alert.title,
            'severity': alert.severity,
            'total_sent': alert.total_sent,
            'total_read': alert.total_read,
            'total_snoozed': alert.total_snoozed,
            'read_rate': (alert.total_read / alert.total_sent * 100) if alert.total_sent > 0 else 0
        })
    
    return Response({
        'summary': {
            'total_alerts_created': total_alerts,
            'active_alerts': active_alerts,
            'total_deliveries': total_deliveries,
            'successful_deliveries': successful_deliveries,
            'delivery_success_rate': (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0,
            'total_read': read_count,
            'total_snoozed': snoozed_count,
            'read_rate': (read_count / total_preferences * 100) if total_preferences > 0 else 0
        },
        'severity_breakdown': list(severity_breakdown),
        'top_performing_alerts': alert_performance_data
    })