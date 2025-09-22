from django.db import models
from django.contrib.auth import get_user_model
from users.models import Team
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class Alert(models.Model):
    """Main alert model - represents an announcement/notification"""
    
    SEVERITY_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
    ]
    
    DELIVERY_TYPE_CHOICES = [
        ('IN_APP', 'In-App'),
        ('EMAIL', 'Email'),  # Future scope
        ('SMS', 'SMS'),      # Future scope
    ]
    
    VISIBILITY_CHOICES = [
        ('ORGANIZATION', 'Entire Organization'),
        ('TEAM', 'Specific Teams'),
        ('USER', 'Specific Users'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='INFO')
    delivery_type = models.CharField(max_length=10, choices=DELIVERY_TYPE_CHOICES, default='IN_APP')
    visibility_type = models.CharField(max_length=15, choices=VISIBILITY_CHOICES)
    
    # Timing
    start_time = models.DateTimeField(default=timezone.now)
    expiry_time = models.DateTimeField()
    reminder_frequency_hours = models.IntegerField(default=2)
    
    # Configuration
    reminders_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Relationships
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_alerts')
    target_teams = models.ManyToManyField(Team, blank=True, related_name='alerts')
    target_users = models.ManyToManyField(User, blank=True, related_name='targeted_alerts')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.severity})"
    
    @property
    def is_expired(self):
        """Check if alert has expired"""
        return timezone.now() > self.expiry_time
    
    @property
    def is_currently_active(self):
        """Check if alert is currently active (not expired and active)"""
        return self.is_active and not self.is_expired
    
    def get_target_users(self):
        """Get all users who should receive this alert"""
        users = set()
        
        if self.visibility_type == 'ORGANIZATION':
            # All users in the organization
            users.update(User.objects.all())
        elif self.visibility_type == 'TEAM':
            # Users in specific teams
            for team in self.target_teams.all():
                users.update(team.members.all())
        elif self.visibility_type == 'USER':
            # Specific users
            users.update(self.target_users.all())
        
        return list(users)
    
    class Meta:
        ordering = ['-created_at']

class UserAlertPreference(models.Model):
    """Tracks user's interaction with each alert"""
    
    STATUS_CHOICES = [
        ('UNREAD', 'Unread'),
        ('READ', 'Read'),
        ('SNOOZED', 'Snoozed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='UNREAD')
    
    # Timing
    first_delivered_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    snoozed_until = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.alert.title} ({self.status})"
    
    @property
    def is_snoozed(self):
        """Check if alert is currently snoozed"""
        if not self.snoozed_until:
            return False
        return timezone.now() < self.snoozed_until
    
    def snooze_for_day(self):
        """Snooze alert until end of current day"""
        end_of_day = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        self.snoozed_until = end_of_day
        self.status = 'SNOOZED'
        self.save()
    
    class Meta:
        unique_together = ['user', 'alert']
        ordering = ['-first_delivered_at']

class NotificationDelivery(models.Model):
    """Log of each notification sent to a user"""
    
    DELIVERY_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('READ', 'Read'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    delivery_method = models.CharField(max_length=10, default='IN_APP')
    status = models.CharField(max_length=10, choices=DELIVERY_STATUS_CHOICES, default='PENDING')
    
    # Timing
    scheduled_at = models.DateTimeField()
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    attempt_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.alert.title} ({self.status})"
    
    def mark_as_sent(self):
        """Mark delivery as sent"""
        self.status = 'SENT'
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_msg=""):
        """Mark delivery as failed"""
        self.status = 'FAILED'
        self.error_message = error_msg
        self.attempt_count += 1
        self.save()
    
    class Meta:
        ordering = ['-scheduled_at']