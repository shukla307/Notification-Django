from django.urls import path
from . import admin_views, user_views

urlpatterns = [
    # Admin URLs
    path('admin/alerts/', admin_views.AdminAlertListCreateView.as_view(), name='admin-alert-list'),
    path('admin/alerts/<int:pk>/', admin_views.AdminAlertDetailView.as_view(), name='admin-alert-detail'),
    path('admin/trigger-reminders/', admin_views.trigger_reminders, name='trigger-reminders'),
    
    # User URLs
    path('user/alerts/', user_views.UserAlertListView.as_view(), name='user-alert-list'),
    path('user/alerts/<int:alert_id>/snooze/', user_views.snooze_alert, name='snooze-alert'),
    path('user/alerts/<int:alert_id>/read/', user_views.mark_alert_read, name='mark-alert-read'),
    path('user/preferences/', user_views.UserAlertPreferenceListView.as_view(), name='user-preferences'),
]