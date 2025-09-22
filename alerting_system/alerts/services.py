from abc import ABC, abstractmethod
from django.utils import timezone
from datetime import timedelta
from .models import Alert, UserAlertPreference, NotificationDelivery
from users.models import User

class NotificationChannel(ABC):
    """Abstract base class for notification channels"""
    
    @abstractmethod
    def send_notification(self, user, alert):
        """Send notification to user"""
        pass

class InAppNotificationChannel(NotificationChannel):
    """In-app notification channel"""
    
    def send_notification(self, user, alert):
        """Send in-app notification"""
        # Create or update user alert preference
        preference, created = UserAlertPreference.objects.get_or_create(
            user=user,
            alert=alert,
            defaults={'status': 'UNREAD'}
        )
        
        # Create notification delivery record
        delivery = NotificationDelivery.objects.create(
            user=user,
            alert=alert,
            delivery_method='IN_APP',
            scheduled_at=timezone.now(),
            status='SENT',
            delivered_at=timezone.now()
        )
        
        return delivery

class EmailNotificationChannel(NotificationChannel):
    """Email notification channel (Future scope)"""
    
    def send_notification(self, user, alert):
        # Future implementation
        print(f"Email notification sent to {user.email}: {alert.title}")
        return None

class SMSNotificationChannel(NotificationChannel):
    """SMS notification channel (Future scope)"""
    
    def send_notification(self, user, alert):
        # Future implementation
        print(f"SMS notification sent to {user.username}: {alert.title}")
        return None

class AlertService:
    """Main service for handling alert operations"""
    
    def __init__(self):
        self.channels = {
            'IN_APP': InAppNotificationChannel(),
            'EMAIL': EmailNotificationChannel(),
            'SMS': SMSNotificationChannel(),
        }
    
    def create_alert(self, admin_user, alert_data):
        """Create a new alert"""
        if not admin_user.is_admin:
            raise PermissionError("Only admins can create alerts")
        
        alert = Alert.objects.create(
            created_by=admin_user,
            **alert_data
        )
        
        # Send initial notifications
        self.send_alert_to_users(alert)
        
        return alert
    
    def send_alert_to_users(self, alert):
        """Send alert to all target users"""
        target_users = alert.get_target_users()
        channel = self.channels.get(alert.delivery_type)
        
        if not channel:
            raise ValueError(f"Unsupported delivery type: {alert.delivery_type}")
        
        deliveries = []
        for user in target_users:
            try:
                delivery = channel.send_notification(user, alert)
                if delivery:
                    deliveries.append(delivery)
            except Exception as e:
                print(f"Failed to send alert to {user.username}: {e}")
        
        return deliveries
    
    def send_reminders(self):
        """Send reminders for active alerts"""
        now = timezone.now()
        
        # Get active alerts that need reminders
        active_alerts = Alert.objects.filter(
            is_active=True,
            expiry_time__gt=now,
            reminders_enabled=True
        )
        
        for alert in active_alerts:
            self.process_alert_reminders(alert)
    
    def process_alert_reminders(self, alert):
        """Process reminders for a specific alert"""
        now = timezone.now()
        target_users = alert.get_target_users()
        
        for user in target_users:
            preference = UserAlertPreference.objects.filter(
                user=user,
                alert=alert
            ).first()
            
            if not preference:
                continue
            
            # Skip if user has snoozed the alert
            if preference.is_snoozed:
                continue
            
            # Check if it's time for a reminder
            last_delivery = NotificationDelivery.objects.filter(
                user=user,
                alert=alert,
                status='SENT'
            ).order_by('-delivered_at').first()
            
            if last_delivery:
                time_since_last = now - last_delivery.delivered_at
                if time_since_last >= timedelta(hours=alert.reminder_frequency_hours):
                    # Send reminder
                    channel = self.channels.get(alert.delivery_type)
                    if channel:
                        channel.send_notification(user, alert)
    
    def snooze_alert(self, user, alert_id):
        """Snooze an alert for a user"""
        try:
            alert = Alert.objects.get(id=alert_id, is_active=True)
            preference = UserAlertPreference.objects.get(
                user=user,
                alert=alert
            )
            preference.snooze_for_day()
            return preference
        except (Alert.DoesNotExist, UserAlertPreference.DoesNotExist):
            raise ValueError("Alert not found or not accessible")
    
    def mark_alert_as_read(self, user, alert_id):
        """Mark an alert as read for a user"""
        try:
            alert = Alert.objects.get(id=alert_id, is_active=True)
            preference = UserAlertPreference.objects.get(
                user=user,
                alert=alert
            )
            preference.status = 'READ'
            preference.last_read_at = timezone.now()
            preference.save()
            return preference
        except (Alert.DoesNotExist, UserAlertPreference.DoesNotExist):
            raise ValueError("Alert not found or not accessible")