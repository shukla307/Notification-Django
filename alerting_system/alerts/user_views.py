from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import Alert, UserAlertPreference
from .serializers import UserAlertSerializer, UserAlertPreferenceSerializer
from .services import AlertService

class UserAlertListView(generics.ListAPIView):
    """User view for listing their alerts"""
    
    serializer_class = UserAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get all active alerts that target this user
        user_alerts = []
        
        # Organization-wide alerts
        org_alerts = Alert.objects.filter(
            visibility_type='ORGANIZATION',
            is_active=True,
            expiry_time__gt=timezone.now()
        )
        user_alerts.extend(org_alerts)
        
        # Team-specific alerts
        if user.team:
            team_alerts = Alert.objects.filter(
                visibility_type='TEAM',
                target_teams=user.team,
                is_active=True,
                expiry_time__gt=timezone.now()
            )
            user_alerts.extend(team_alerts)
        
        # User-specific alerts
        specific_alerts = Alert.objects.filter(
            visibility_type='USER',
            target_users=user,
            is_active=True,
            expiry_time__gt=timezone.now()
        )
        user_alerts.extend(specific_alerts)
        
        # Remove duplicates
        unique_alerts = list(set(user_alerts))
        
        return unique_alerts

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def snooze_alert(request, alert_id):
    """Snooze an alert for the current user"""
    try:
        alert_service = AlertService()
        preference = alert_service.snooze_alert(request.user, alert_id)
        
        serializer = UserAlertPreferenceSerializer(preference)
        return Response(serializer.data)
        
    except ValueError as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": "Failed to snooze alert"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_alert_read(request, alert_id):
    """Mark an alert as read for the current user"""
    try:
        alert_service = AlertService()
        preference = alert_service.mark_alert_as_read(request.user, alert_id)
        
        serializer = UserAlertPreferenceSerializer(preference)
        return Response(serializer.data)
        
    except ValueError as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": "Failed to mark alert as read"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class UserAlertPreferenceListView(generics.ListAPIView):
    """User view for their alert preferences/history"""
    
    serializer_class = UserAlertPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserAlertPreference.objects.filter(
            user=self.request.user
        ).select_related('alert')