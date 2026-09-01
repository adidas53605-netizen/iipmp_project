from datetime import date, timedelta
from decimal import Decimal
from .models import Alert

def compute_risk_level(project):
    if project.status == 'completed':
        return 'low'
    
    today = date.today()
    risk = 'low'
    
    if project.expected_completion < today and project.status != 'completed':
        risk = 'high'
        
    cost_overrun_pct = project.cost_overrun_percentage
    if cost_overrun_pct > 30:
        risk = 'high'
    elif cost_overrun_pct > 15 and risk != 'high':
        risk = 'medium'
        
    phys_prog = float(project.physical_progress)
    exp_prog = project.expected_progress
    if phys_prog < exp_prog - 20:
        risk = 'high'
    elif phys_prog < exp_prog - 10 and risk != 'high':
        risk = 'medium'
        
    eff_cost = float(project.effective_cost)
    expenditure = float(project.expenditure)
    if expenditure > eff_cost * 0.9 and phys_prog < 70:
        risk = 'high'
        
    return risk

def detect_delay(project):
    today = date.today()
    is_delayed = project.expected_completion < today and project.status != 'completed'
    delay_months = project.delay_months
    message = f"Delayed by {delay_months} months" if is_delayed else ""
    
    return {
        'is_delayed': is_delayed,
        'delay_months': delay_months,
        'message': message
    }

def compute_cost_overrun(project):
    overrun_amount = project.cost_overrun
    has_overrun = overrun_amount > 0
    overrun_percentage = project.cost_overrun_percentage
    message = f"Cost overrun of {overrun_percentage}% (₹ {overrun_amount} Cr)" if has_overrun else ""
    
    return {
        'has_overrun': has_overrun,
        'overrun_amount': overrun_amount,
        'overrun_percentage': overrun_percentage,
        'message': message
    }

def generate_alerts(project):
    Alert.objects.filter(project=project).delete()
    today = date.today()
    
    delay_info = detect_delay(project)
    if delay_info['is_delayed']:
        Alert.objects.create(
            project=project,
            alert_type='delay',
            severity='danger',
            message=delay_info['message']
        )
        
    cost_info = compute_cost_overrun(project)
    if cost_info['overrun_percentage'] > 10:
        sev = 'danger' if cost_info['overrun_percentage'] > 25 else 'warning'
        Alert.objects.create(
            project=project,
            alert_type='cost_overrun',
            severity=sev,
            message=cost_info['message']
        )
        
    phys_prog = float(project.physical_progress)
    exp_prog = project.expected_progress
    if phys_prog < exp_prog - 15:
        Alert.objects.create(
            project=project,
            alert_type='progress_gap',
            severity='warning',
            message=f"Physical progress is {phys_prog}% but expected is {exp_prog:.1f}%"
        )
        
    if project.status != 'completed' and project.expected_completion > today and (project.expected_completion - today).days <= 90:
        Alert.objects.create(
            project=project,
            alert_type='deadline_approaching',
            severity='info',
            message="Expected completion is within 3 months"
        )
        
    for milestone in project.milestones.all():
        if milestone.status == 'completed' and milestone.completion_date:
            if (today - milestone.completion_date).days <= 30:
                Alert.objects.create(
                    project=project,
                    alert_type='milestone_completed',
                    severity='success',
                    message=f"Milestone '{milestone.name}' completed recently."
                )
                
    if project.risk_level == 'high':
        Alert.objects.create(
            project=project,
            alert_type='high_risk',
            severity='danger',
            message="Project is at High Risk"
        )

def update_project_automation(project):
    project.risk_level = compute_risk_level(project)
    
    delay_info = detect_delay(project)
    if delay_info['is_delayed'] and project.status == 'ongoing':
        project.status = 'delayed'
        
    if project.physical_progress >= 100:
        project.status = 'completed'
        project.physical_progress = 100
        
    project.save(update_fields=['risk_level', 'status', 'physical_progress'])
    
    generate_alerts(project)
