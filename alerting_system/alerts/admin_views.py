from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from datetime import datetime
from .models import Alert
from .serializers import AlertSerializer, AlertCreateSerializer
from .services import AlertService

class AdminAlertListCreateView(generics.ListCreateAPIView):
    """Admin view for listing and creating alerts"""
    
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_admin:
            return Alert.objects.none()
        
        queryset = Alert.objects.all()
        
        # Filtering
        severity = self.request.query_params.get('severity')
        status_filter = self.request.query_params.get('status')
        
        if severity:
            queryset = queryset.filter(severity=severity.upper())
        
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True, expiry_time__gt=timezone.now())
        elif status_filter == 'expired':
            queryset = queryset.filter(expiry_time__lte=timezone.now())
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AlertCreateSerializer
        return AlertSerializer
    
    def perform_create(self, serializer):
        if not self.request.user.is_admin:
            raise PermissionError("Only admins can create alerts")
        
        alert_service = AlertService()
        alert_data = serializer.validated_data
        
        # Extract many-to-many relationships
        target_teams = alert_data.pop('target_teams', [])
        target_users = alert_data.pop('target_users', [])
        
        # Create the alert
        alert = alert_service.create_alert(self.request.user, alert_data)
        
        # Set relationships
        if target_teams:
            alert.target_teams.set(target_teams)
        if target_users:
            alert.target_users.set(target_users)
        
        alert.save()

class AdminAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin view for managing individual alerts"""
    
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_admin:
            return Alert.objects.none()
        return Alert.objects.all()
    
    def perform_destroy(self, instance):
        # Instead of deleting, we archive the alert
        instance.is_active = False
        instance.save()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_reminders(request):
    """Manually trigger reminder sending (for testing)"""
    if not request.user.is_admin:
        return Response(
            {"error": "Only admins can trigger reminders"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    alert_service = AlertService()
    alert_service.send_reminders()
    
    return Response({"message": "Reminders triggered successfully"})