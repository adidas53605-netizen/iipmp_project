from django.db import models
from datetime import date

STATUS_CHOICES = [
    ('not_started', 'Not Started'),
    ('ongoing', 'Ongoing'),
    ('completed', 'Completed'),
    ('delayed', 'Delayed')
]

RISK_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High')
]

MILESTONE_STATUS_CHOICES = [
    ('completed', 'Completed'),
    ('in_progress', 'In Progress'),
    ('pending', 'Pending')
]

ALERT_TYPE_CHOICES = [
    ('delay', 'Project Delayed'),
    ('cost_overrun', 'Cost Overrun'),
    ('progress_gap', 'Progress Below Expected'),
    ('deadline_approaching', 'Deadline Approaching'),
    ('milestone_completed', 'Milestone Completed'),
    ('high_risk', 'High Risk Detected')
]

SEVERITY_CHOICES = [
    ('info', 'Info'),
    ('warning', 'Warning'),
    ('danger', 'Danger'),
    ('success', 'Success')
]

class Project(models.Model):
    project_id = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=300)
    ministry = models.CharField(max_length=200, db_index=True)
    department = models.CharField(max_length=200, blank=True, default='')
    state = models.CharField(max_length=100, db_index=True)
    district = models.CharField(max_length=100, blank=True, default='', db_index=True)
    implementing_agency = models.CharField(max_length=300)
    approved_cost = models.DecimalField(max_digits=12, decimal_places=2)
    revised_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expenditure = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField()
    expected_completion = models.DateField(db_index=True)
    physical_progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    financial_progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', db_index=True)
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES, default='low', db_index=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def cost_overrun(self):
        if self.revised_cost and self.revised_cost > self.approved_cost:
            return self.revised_cost - self.approved_cost
        return 0

    @property
    def cost_overrun_percentage(self):
        if self.approved_cost > 0:
            return round((self.cost_overrun / self.approved_cost) * 100, 1)
        return 0

    @property
    def delay_months(self):
        today = date.today()
        if self.status != 'completed' and self.expected_completion < today:
            diff = today - self.expected_completion
            return max(0, diff.days // 30)
        return 0

    @property
    def effective_cost(self):
        return self.revised_cost if self.revised_cost else self.approved_cost

    @property
    def is_delayed(self):
        today = date.today()
        return self.expected_completion < today and self.status != 'completed'

    @property
    def expected_progress(self):
        today = date.today()
        if today < self.start_date:
            return 0
        if today > self.expected_completion:
            return 100
        
        total_days = (self.expected_completion - self.start_date).days
        elapsed_days = (today - self.start_date).days
        
        if total_days <= 0:
            return 100
            
        progress = (elapsed_days / total_days) * 100
        return min(progress, 100)

    def __str__(self):
        return f'{self.project_id} - {self.name}'

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['state', 'district']),
            models.Index(fields=['status', 'risk_level']),
            models.Index(fields=['ministry', 'status']),
        ]

class Milestone(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=200)
    target_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=MILESTONE_STATUS_CHOICES, default='pending')
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.name} ({self.project.project_id})'

    class Meta:
        ordering = ['order']

class Alert(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='info')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.alert_type}: {self.project.project_id}'

    class Meta:
        ordering = ['-created_at']

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('ministry_official', 'Ministry Official'),
    ('field_officer', 'Field Officer'),
    ('auditor', 'Auditor'),
    ('nodal_officer', 'Nodal Officer'),
    ('public_viewer', 'Public Viewer'),
]

DASHBOARD_VIEW_CHOICES = [
    ('overview', 'Executive Overview'),
    ('financial', 'Financial & Budget'),
    ('map', 'State & Regional Map'),
    ('analytics', 'Analytics & Risk'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150, blank=True, default='')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='nodal_officer')
    phone = models.CharField(max_length=20, blank=True, default='')
    designation = models.CharField(max_length=100, blank=True, default='')
    ministry = models.CharField(max_length=200, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    employee_id = models.CharField(max_length=50, blank=True, default='')
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    email_notifications = models.BooleanField(default=True)
    default_dashboard_view = models.CharField(max_length=50, choices=DASHBOARD_VIEW_CHOICES, default='overview')
    profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    mfa_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=64, blank=True, default='')
    must_reset_password = models.BooleanField(default=False)

    @property
    def display_name(self):
        if self.full_name and self.full_name.strip():
            return self.full_name.strip()
        if self.user.first_name and self.user.first_name.strip():
            return self.user.first_name.strip()
        if self.user.email:
            return self.user.email.split('@')[0].replace('.', ' ').replace('_', ' ').title()
        return self.user.username

    @property
    def avatar_letter(self):
        name = self.display_name
        return name[0].upper() if name else 'U'

    @property
    def completion_percentage(self):
        fields_to_check = [
            self.full_name,
            self.phone,
            self.designation,
            self.ministry,
            self.state,
            self.employee_id,
            self.photo,
            self.user.email,
        ]
        filled = sum(1 for val in fields_to_check if val)
        return int(round((filled / len(fields_to_check)) * 100))

    def __str__(self):
        return f'{self.display_name} ({self.get_role_display()})'

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

class FailedLoginAttempt(models.Model):
    identifier = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    failed_count = models.IntegerField(default=0)
    last_failed_at = models.DateTimeField(auto_now=True)
    locked_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.identifier}: {self.failed_count} failures'

