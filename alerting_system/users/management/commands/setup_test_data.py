from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Team
from alerts.models import Alert
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test data for the alerting system'
    
    def handle(self, *args, **options):
        self.stdout.write("Creating test data...")
        
        # Create teams
        teams_data = [
            {'name': 'Engineering', 'description': 'Software development team'},
            {'name': 'Marketing', 'description': 'Marketing and communications team'},
            {'name': 'Sales', 'description': 'Sales and business development team'},
            {'name': 'HR', 'description': 'Human resources team'},
        ]
        
        teams = {}
        for team_data in teams_data:
            team, created = Team.objects.get_or_create(
                name=team_data['name'],
                defaults={'description': team_data['description']}
            )
            teams[team.name] = team
            if created:
                self.stdout.write(f"Created team: {team.name}")
        
        # Create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@company.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_admin': True,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write("Created admin user (username: admin, password: admin123)")
        
        # Create regular users
        users_data = [
            {'username': 'john_eng', 'first_name': 'John', 'last_name': 'Smith', 'team': 'Engineering'},
            {'username': 'sarah_eng', 'first_name': 'Sarah', 'last_name': 'Johnson', 'team': 'Engineering'},
            {'username': 'mike_marketing', 'first_name': 'Mike', 'last_name': 'Davis', 'team': 'Marketing'},
            {'username': 'lisa_marketing', 'first_name': 'Lisa', 'last_name': 'Wilson', 'team': 'Marketing'},
            {'username': 'tom_sales', 'first_name': 'Tom', 'last_name': 'Brown', 'team': 'Sales'},
            {'username': 'anna_hr', 'first_name': 'Anna', 'last_name': 'Taylor', 'team': 'HR'},
        ]
        
        for user_data in users_data:
            team_name = user_data.pop('team')
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': f"{user_data['username']}@company.com",
                    'team': teams[team_name],
                    **user_data
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f"Created user: {user.username}")
        
        # Create sample alerts
        now = timezone.now()
        alerts_data = [
            {
                'title': 'System Maintenance Scheduled',
                'message': 'Our servers will undergo maintenance tonight from 10 PM to 2 AM. Please save your work.',
                'severity': 'WARNING',
                'visibility_type': 'ORGANIZATION',
                'expiry_time': now + timedelta(days=1),
            },
            {
                'title': 'New Security Policy',
                'message': 'Please review the new security policy document in your email.',
                'severity': 'INFO',
                'visibility_type': 'ORGANIZATION',
                'expiry_time': now + timedelta(days=7),
            },
            {
                'title': 'Engineering Team Meeting',
                'message': 'Mandatory team meeting tomorrow at 10 AM in Conference Room A.',
                'severity': 'CRITICAL',
                'visibility_type': 'TEAM',
                'expiry_time': now + timedelta(days=1),
            },
            {
                'title': 'Marketing Campaign Launch',
                'message': 'The new product campaign goes live tomorrow. All hands on deck!',
                'severity': 'WARNING',
                'visibility_type': 'TEAM',
                'expiry_time': now + timedelta(days=2),
            },
        ]
        
        from alerts.services import AlertService
        alert_service = AlertService()
        
        for i, alert_data in enumerate(alerts_data):
            alert, created = Alert.objects.get_or_create(
                title=alert_data['title'],
                defaults={
                    'created_by': admin,
                    **alert_data
                }
            )
            
            if created:
                # Set team targets for team-specific alerts
                if alert.visibility_type == 'TEAM':
                    if 'Engineering' in alert.title:
                        alert.target_teams.add(teams['Engineering'])
                    elif 'Marketing' in alert.title:
                        alert.target_teams.add(teams['Marketing'])
                
                # Send the alert
                alert_service.send_alert_to_users(alert)
                self.stdout.write(f"Created alert: {alert.title}")
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created test data!')
        )
        self.stdout.write("You can now login with:")
        self.stdout.write("- Admin: username='admin', password='admin123'")
    
        self.stdout.write("- Users: password='password123' for all users")