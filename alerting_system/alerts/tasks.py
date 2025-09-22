from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .services import AlertService

@shared_task
def send_reminders():
    """Background task to send alert reminders"""
    print("Running reminder task...")
    alert_service = AlertService()
    try:
        alert_service.send_reminders()
        print("Reminders sent successfully")
        return "Success"
    except Exception as e:
        print(f"Error sending reminders: {e}")
        return f"Error: {e}"

@shared_task
def send_alert_to_users_async(alert_id):
    """Send alert to users asynchronously"""
    from .models import Alert
    try:
        alert = Alert.objects.get(id=alert_id)
        alert_service = AlertService()
        alert_service.send_alert_to_users(alert)
        return f"Alert {alert_id} sent successfully"
    except Alert.DoesNotExist:
        return f"Alert {alert_id} not found"
    except Exception as e:
        return f"Error sending alert {alert_id}: {e}"
    
    