from rest_framework import serializers
from .models import Alert, UserAlertPreference, NotificationDelivery
from users.models import Team, User

class AlertSerializer(serializers.ModelSerializer):
    """Serializer for Alert model"""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    target_team_names = serializers.StringRelatedField(source='target_teams', many=True, read_only=True)
    target_user_names = serializers.StringRelatedField(source='target_users', many=True, read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_currently_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']

class AlertCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alerts"""
    
    class Meta:
        model = Alert
        fields = [
            'title', 'message', 'severity', 'delivery_type', 'visibility_type',
            'start_time', 'expiry_time', 'reminder_frequency_hours', 
            'reminders_enabled', 'target_teams', 'target_users'
        ]

class UserAlertSerializer(serializers.ModelSerializer):
    """Serializer for user-facing alert data"""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    user_preference = serializers.SerializerMethodField()
    
    class Meta:
        model = Alert
        fields = [
            'id', 'title', 'message', 'severity', 'created_by_username',
            'start_time', 'expiry_time', 'created_at', 'user_preference'
        ]
    
    def get_user_preference(self, obj):
        """Get user's preference for this alert"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                preference = UserAlertPreference.objects.get(
                    user=request.user,
                    alert=obj
                )
                return {
                    'status': preference.status,
                    'is_snoozed': preference.is_snoozed,
                    'last_read_at': preference.last_read_at,
                    'snoozed_until': preference.snoozed_until
                }
            except UserAlertPreference.DoesNotExist:
                return {
                    'status': 'UNREAD',
                    'is_snoozed': False,
                    'last_read_at': None,
                    'snoozed_until': None
                }
        return None

class UserAlertPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user alert preferences"""
    
    alert_title = serializers.CharField(source='alert.title', read_only=True)
    alert_severity = serializers.CharField(source='alert.severity', read_only=True)
    is_snoozed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserAlertPreference
        fields = [
            'id', 'alert', 'alert_title', 'alert_severity', 'status',
            'first_delivered_at', 'last_read_at', 'snoozed_until', 'is_snoozed'
        ]
