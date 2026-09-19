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
        if self.status in ['ongoing', 'delayed'] and self.expected_completion < today:
            diff = today - self.expected_completion
            return diff.days // 30
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

ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('ministry_official', 'Ministry Official'),
    ('field_officer', 'Field Officer'),
    ('auditor', 'Auditor'),
    ('public_viewer', 'Public Viewer'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='public_viewer')
    phone = models.CharField(max_length=20, blank=True, default='')
    mfa_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=64, blank=True, default='')
    must_reset_password = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'

class FailedLoginAttempt(models.Model):
    identifier = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    failed_count = models.IntegerField(default=0)
    last_failed_at = models.DateTimeField(auto_now=True)
    locked_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.identifier}: {self.failed_count} failures'

