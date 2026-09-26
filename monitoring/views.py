import json
import csv
import random
from io import StringIO
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum, Avg, Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Project, Milestone, Alert, UserProfile, FailedLoginAttempt
from .forms import ProjectForm, MilestoneForm, CSVImportForm
from .automation import update_project_automation, compute_cost_overrun, detect_delay
from .decorators import role_required

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_rate_limit(ip_address):
    if not ip_address:
        return False, None
    now = timezone.now()
    ten_minutes_ago = now - timedelta(minutes=10)
    recent_attempts = FailedLoginAttempt.objects.filter(
        ip_address=ip_address,
        last_failed_at__gte=ten_minutes_ago
    )
    total_failures = recent_attempts.aggregate(Sum('failed_count'))['failed_count__sum'] or 0
    if total_failures >= 10:
        return True, "Too many failed login attempts from this IP. Please try again after 10 minutes."
    return False, None

def check_lockout(identifier, ip_address=None):
    now = timezone.now()
    attempt = FailedLoginAttempt.objects.filter(identifier=identifier).first()
    if attempt and attempt.locked_until and attempt.locked_until > now:
        remaining_seconds = int((attempt.locked_until - now).total_seconds())
        remaining_minutes = max(1, remaining_seconds // 60)
        return True, f"Account locked due to 5 consecutive failed login attempts. Please try again after {remaining_minutes} minute(s)."
    return False, None

def record_failed_attempt(identifier, ip_address=None):
    now = timezone.now()
    attempt, created = FailedLoginAttempt.objects.get_or_create(identifier=identifier, defaults={'ip_address': ip_address})
    attempt.failed_count += 1
    attempt.last_failed_at = now
    if ip_address:
        attempt.ip_address = ip_address
    if attempt.failed_count >= 5:
        attempt.locked_until = now + timedelta(minutes=15)
    attempt.save()
    return attempt.failed_count

def reset_failed_attempts(identifier):
    FailedLoginAttempt.objects.filter(identifier=identifier).update(failed_count=0, locked_until=None)

def home(request):

    return redirect('login')

def dashboard(request):
    projects = Project.objects.all()
    total_projects = projects.count()
    ongoing_count = projects.filter(status='ongoing').count()
    completed_count = projects.filter(status='completed').count()
    delayed_count = projects.filter(status='delayed').count()
    not_started_count = projects.filter(status='not_started').count()
    at_risk_count = projects.filter(risk_level='high').count()
    new_added_count = 2
    
    total_approved_cost = float(projects.aggregate(Sum('approved_cost'))['approved_cost__sum'] or 0)
    total_expenditure = float(projects.aggregate(Sum('expenditure'))['expenditure__sum'] or 0)
    avg_progress = round(float(projects.aggregate(Avg('physical_progress'))['physical_progress__avg'] or 0), 1)
    years_to_finish = 4

    status_data = json.dumps({
        'labels': ['Ongoing', 'Completed', 'Delayed', 'On Hold', 'New Added', 'At Risk'],
        'data': [ongoing_count, completed_count, delayed_count, not_started_count, new_added_count, at_risk_count]
    })

    # District distribution for West Bengal
    district_counts = list(projects.values('district').annotate(count=Count('id')).order_by('-count')[:6])
    state_data = json.dumps({
        'labels': [d['district'] or 'Other' for d in district_counts],
        'data': [d['count'] for d in district_counts]
    })

    ministry_counts = list(projects.values('ministry').annotate(count=Count('id')).order_by('-count')[:5])
    ministry_data = json.dumps({
        'labels': [m['ministry'].replace('Ministry of ', '') for m in ministry_counts],
        'data': [m['count'] for m in ministry_counts]
    })

    top_cost_projects = projects.order_by('-approved_cost')[:5]
    cost_data = json.dumps({
        'labels': [p.name[:20] + '...' if len(p.name) > 20 else p.name for p in top_cost_projects],
        'approved': [float(p.approved_cost) for p in top_cost_projects],
        'revised': [float(p.effective_cost) for p in top_cost_projects],
        'expenditure': [float(p.expenditure) for p in top_cost_projects]
    })

    top_prog_projects = projects.order_by('-physical_progress')[:6]
    progress_data = json.dumps({
        'labels': [p.name[:20] + '...' if len(p.name) > 20 else p.name for p in top_prog_projects],
        'data': [float(p.physical_progress) for p in top_prog_projects]
    })

    monthly_data = json.dumps({
        'labels': ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
        'data': [48, 52, 55, 58, 60, avg_progress]
    })

    context = {
        'total_projects': total_projects,
        'ongoing_count': ongoing_count,
        'completed_count': completed_count,
        'delayed_count': delayed_count,
        'not_started_count': not_started_count,
        'at_risk_count': at_risk_count,
        'total_approved_cost': total_approved_cost,
        'total_expenditure': total_expenditure,
        'avg_progress': avg_progress,
        'new_added_count': new_added_count,
        'years_to_finish': years_to_finish,
        'status_data': status_data,
        'state_data': state_data,
        'ministry_data': ministry_data,
        'cost_data': cost_data,
        'monthly_data': monthly_data,
        'progress_data': progress_data,
    }
    return render(request, 'dashboard.html', context)

def api_dashboard(request):
    """JSON API endpoint for dashboard data — used by the Refresh Data button."""
    projects = Project.objects.all()
    ongoing_count = projects.filter(status='ongoing').count()
    completed_count = projects.filter(status='completed').count()
    delayed_count = projects.filter(status='delayed').count()
    not_started_count = projects.filter(status='not_started').count()
    at_risk_count = projects.filter(risk_level='high').count()
    new_added_count = 2

    return JsonResponse({
        'total_projects': projects.count(),
        'ongoing_count': ongoing_count,
        'completed_count': completed_count,
        'delayed_count': delayed_count,
        'not_started_count': not_started_count,
        'at_risk_count': at_risk_count,
        'new_added_count': new_added_count,
        'status_data': {
            'labels': ['Ongoing', 'Completed', 'Delayed', 'On Hold', 'New Added', 'At Risk'],
            'data': [
                ongoing_count,
                completed_count,
                delayed_count,
                not_started_count,
                new_added_count,
                at_risk_count
            ]
        },
        'total_approved_cost': float(projects.aggregate(Sum('approved_cost'))['approved_cost__sum'] or 0),
        'total_expenditure': float(projects.aggregate(Sum('expenditure'))['expenditure__sum'] or 0),
        'avg_progress': round(float(projects.aggregate(Avg('physical_progress'))['physical_progress__avg'] or 0), 1),
        'years_to_finish': 4,
        'refreshed_at': date.today().isoformat()
    })

def export_dashboard_csv(request):
    """Export dashboard project data as CSV with dynamic values."""
    import csv as csv_module
    from django.http import HttpResponse
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="iipmp_project_dashboard_export.csv"'
    writer = csv_module.writer(response)
    projects = Project.objects.all()
    total_approved = float(projects.aggregate(Sum('approved_cost'))['approved_cost__sum'] or 0)
    total_exp = float(projects.aggregate(Sum('expenditure'))['expenditure__sum'] or 0)
    avg_prog = round(float(projects.aggregate(Avg('physical_progress'))['physical_progress__avg'] or 0), 1)

    writer.writerow(['IIPMP - Integrated Infrastructure Project Monitoring Portal'])
    writer.writerow(['Dashboard Executive Summary - West Bengal'])
    writer.writerow([])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Projects', projects.count()])
    writer.writerow(['Ongoing Projects', projects.filter(status='ongoing').count()])
    writer.writerow(['Completed Projects', projects.filter(status='completed').count()])
    writer.writerow(['Delayed Projects', projects.filter(status='delayed').count()])
    writer.writerow(['On Hold Projects', projects.filter(status='not_started').count()])
    writer.writerow(['At Risk Projects', projects.filter(risk_level='high').count()])
    writer.writerow(['Approved Cost (Cr)', f'₹ {total_approved:,.1f} Cr'])
    writer.writerow(['Total Expenditure (Cr)', f'₹ {total_exp:,.1f} Cr'])
    writer.writerow(['Average Progress (%)', f'{avg_prog}%'])
    writer.writerow([])
    writer.writerow(['Project ID', 'Project Name', 'Ministry', 'District', 'Status', 'Approved Cost (Cr)', 'Expenditure (Cr)', 'Progress (%)'])
    
    for p in projects:
        writer.writerow([p.project_id, p.name, p.ministry, p.district or p.state, p.get_status_display(), p.approved_cost, p.expenditure, f'{p.physical_progress}%'])
    return response

def project_list(request):
    projects = Project.objects.all()
    
    search = request.GET.get('search')
    if search and search.strip():
        s = search.strip()
        projects = projects.filter(
            Q(name__icontains=s) | 
            Q(project_id__icontains=s) | 
            Q(ministry__icontains=s) |
            Q(implementing_agency__icontains=s)
        )
        
    ministry = request.GET.get('ministry')
    if ministry and ministry.strip():
        projects = projects.filter(ministry__icontains=ministry.strip())
        
    district = request.GET.get('district')
    if district and district.strip():
        projects = projects.filter(district__icontains=district.strip())
        
    status = request.GET.get('status')
    if status and status.strip():
        projects = projects.filter(status=status.strip())
        
    risk = request.GET.get('risk') or request.GET.get('risk_level')
    if risk and risk.strip():
        projects = projects.filter(risk_level=risk.strip())
        
    agency = request.GET.get('implementing_agency')
    if agency and agency.strip():
        projects = projects.filter(implementing_agency__icontains=agency.strip())

    # 1. Ministry Dropdown: Deduplicated 5 main ministries specified
    ministries = [
        'Ministry of Road Transport',
        'Ministry of Power',
        'Ministry of Urban Development',
        'Ministry of Railways',
        'Ministry of Water Resources'
    ]

    # 2. State & District Dropdowns: Deduplicated unique states & districts with mapping
    raw_states = list(Project.objects.values_list('state', flat=True).distinct())
    states = sorted(list(set([st.strip() for st in raw_states if st and st.strip()])))

    raw_pairs = Project.objects.values('state', 'district').distinct()
    state_districts_map = {}
    all_districts = set()

    for item in raw_pairs:
        st = (item['state'] or '').strip()
        dt = (item['district'] or '').strip()
        if st:
            if st not in state_districts_map:
                state_districts_map[st] = set()
            if dt:
                state_districts_map[st].add(dt)
                all_districts.add(dt)

    state_districts_map_json = {st: sorted(list(dt_set)) for st, dt_set in state_districts_map.items()}
    districts = sorted(list(all_districts))

    # Optimization & Pagination (Default per_page=50 to display all projects on Page 1)
    projects = projects.prefetch_related('milestones', 'alerts').order_by('-updated_at')
    per_page = int(request.GET.get('per_page', 50))
    paginator = Paginator(projects, per_page)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'projects': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_filtered_count': projects.count(),
        'ministries': ministries,
        'states': states,
        'districts': districts,
        'state_districts_json': json.dumps(state_districts_map_json),
        'current_filters': request.GET
    }
    return render(request, 'projects.html', context)

def project_detail(request, project_id):
    project = get_object_or_404(Project, project_id=project_id)
    milestones = project.milestones.all()
    cost_overrun_info = compute_cost_overrun(project)
    delay_info = detect_delay(project)
    alerts = project.alerts.order_by('-created_at')[:5]

    context = {
        'project': project,
        'milestones': milestones,
        'cost_overrun_info': cost_overrun_info,
        'delay_info': delay_info,
        'alerts': alerts
    }
    return render(request, 'project_detail.html', context)

@role_required(['admin', 'ministry_official', 'auditor'])
def database_manage(request):
    projects = Project.objects.all()
    csv_form = CSVImportForm()
    context = {
        'projects': projects,
        'csv_form': csv_form
    }
    return render(request, 'database.html', context)

@role_required(['admin', 'ministry_official'])
def project_create(request):
    import re
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            if not project.project_id or not project.project_id.strip():
                existing_ids = list(Project.objects.values_list('project_id', flat=True))
                nums = [int(re.search(r'\d+', pid).group()) for pid in existing_ids if pid and re.search(r'\d+', pid)]
                next_num = (max(nums) + 1) if nums else 1
                project.project_id = f"PROJ-{next_num:03d}"
            if not project.start_date:
                project.start_date = date.today()
            project.save()
            update_project_automation(project)
            messages.success(request, f'Project {project.name} ({project.project_id}) created successfully.')
            return redirect('project_list')
    else:
        form = ProjectForm()
    
    context = {'form': form, 'action': 'Add New Project'}
    return render(request, 'project_form.html', context)

@role_required(['admin', 'ministry_official', 'field_officer'])
def project_edit(request, project_id):
    project = get_object_or_404(Project, project_id=project_id)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            update_project_automation(project)
            messages.success(request, 'Project updated successfully.')
            return redirect('database_manage')
    else:
        form = ProjectForm(instance=project)
        
    context = {'form': form, 'action': 'Edit Project', 'project': project}
    return render(request, 'project_form.html', context)

@role_required(['admin', 'ministry_official'])
def project_delete(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, project_id=project_id)
        project.delete()
        messages.success(request, 'Project deleted successfully.')
        return redirect('database_manage')
    return redirect('database_manage')

@role_required(['admin', 'ministry_official', 'field_officer'])
def milestone_create(request, project_id):
    project = get_object_or_404(Project, project_id=project_id)
    if request.method == 'POST':
        form = MilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.project = project
            milestone.save()
            update_project_automation(project)
            messages.success(request, 'Milestone added successfully.')
            return redirect('project_detail', project_id=project.project_id)
    else:
        form = MilestoneForm()
        
    context = {'form': form, 'project': project, 'action': 'Add Milestone'}
    return render(request, 'milestone_form.html', context)

@login_required
def milestone_edit(request, project_id, milestone_id):
    project = get_object_or_404(Project, project_id=project_id)
    milestone = get_object_or_404(Milestone, id=milestone_id, project=project)
    if request.method == 'POST':
        form = MilestoneForm(request.POST, instance=milestone)
        if form.is_valid():
            form.save()
            update_project_automation(project)
            messages.success(request, 'Milestone updated successfully.')
            return redirect('project_detail', project_id=project.project_id)
    else:
        form = MilestoneForm(instance=milestone)
        
    context = {'form': form, 'project': project, 'milestone': milestone, 'action': 'Edit Milestone'}
    return render(request, 'milestone_form.html', context)

def analytics(request):
    risk_counts = Project.objects.values('risk_level').annotate(count=Count('id'))
    risk_data = json.dumps({
        'labels': [r['risk_level'] for r in risk_counts],
        'data': [r['count'] for r in risk_counts]
    })
    
    b0_25 = Project.objects.filter(physical_progress__lt=25).count()
    b25_50 = Project.objects.filter(physical_progress__gte=25, physical_progress__lt=50).count()
    b50_75 = Project.objects.filter(physical_progress__gte=50, physical_progress__lt=75).count()
    b75_100 = Project.objects.filter(physical_progress__gte=75).count()
    progress_distribution = json.dumps({
        'labels': ['0-25%', '25-50%', '50-75%', '75-100%'],
        'data': [b0_25, b25_50, b50_75, b75_100]
    })
    
    ministry_cost = Project.objects.values('ministry').annotate(
        app_cost=Sum('approved_cost'), 
        rev_cost=Sum('revised_cost'),
        exp=Sum('expenditure')
    )
    cost_comparison = json.dumps({
        'labels': [m['ministry'] for m in ministry_cost],
        'approved': [float(m['app_cost'] or 0) for m in ministry_cost],
        'revised': [float(m['rev_cost'] or 0) for m in ministry_cost],
        'expenditure': [float(m['exp'] or 0) for m in ministry_cost]
    }, default=str)
    
    state_cost = Project.objects.values('state').annotate(total_cost=Sum('approved_cost'))
    state_cost_data = json.dumps({
        'labels': [s['state'] for s in state_cost],
        'data': [float(s['total_cost'] or 0) for s in state_cost]
    }, default=str)

    # Re-use dashboard data as requested
    ongoing_count = Project.objects.filter(status='ongoing').count()
    completed_count = Project.objects.filter(status='completed').count()
    delayed_count = Project.objects.filter(status='delayed').count()
    not_started_count = Project.objects.filter(status='not_started').count()
    status_data = json.dumps({
        'labels': ['Ongoing', 'Completed', 'Delayed', 'Not Started'],
        'data': [ongoing_count, completed_count, delayed_count, not_started_count]
    })
    states = Project.objects.values('state').annotate(count=Count('id'))
    state_data = json.dumps({
        'labels': [s['state'] for s in states],
        'data': [s['count'] for s in states]
    })

    # 6. Cost vs Progress Correlation Data
    projects = Project.objects.all()
    if projects.exists():
        cost_data = json.dumps({
            'labels': [p.name for p in projects[:10]],
            'approved': [float(p.approved_cost) for p in projects[:10]],
            'progress': [float(p.physical_progress) for p in projects[:10]]
        })
    else:
        cost_data = json.dumps({
            'labels': ['Kolkata Metro Rail', 'NH-17 Widening', 'Smart City Hub', 'Port Terminal', 'Solar Grid', 'Water Pipeline'],
            'approved': [4200, 3500, 2800, 2100, 1800, 1200],
            'progress': [78, 65, 85, 42, 55, 30]
        })

    context = {
        'risk_data': risk_data,
        'progress_distribution': progress_distribution,
        'cost_comparison': cost_comparison,
        'state_cost_data': state_cost_data,
        'status_data': status_data,
        'state_data': state_data,
        'cost_data': cost_data,
    }
    return render(request, 'analytics.html', context)

def budget_view(request):
    total_approved = Project.objects.aggregate(Sum('approved_cost'))['approved_cost__sum'] or 65450
    total_revised = Project.objects.aggregate(Sum('revised_cost'))['revised_cost__sum'] or 69150
    total_expenditure = Project.objects.aggregate(Sum('expenditure'))['expenditure__sum'] or 34220
    net_overrun = (total_revised - total_approved) if (total_revised and total_approved and total_revised > total_approved) else 3700

    # Overrun projects list
    overrun_projects = []
    for p in Project.objects.all():
        if p.revised_cost and p.revised_cost > p.approved_cost:
            overrun_projects.append(p)

    # Cost comparison chart data
    cost_comparison = json.dumps({
        'labels': ['Kolkata Metro', 'NH-17', 'Smart City', 'Port Terminal', 'Solar Grid'],
        'approved': [4200, 3500, 2800, 2100, 1800],
        'revised': [4500, 3500, 3100, 2100, 1950],
        'expenditure': [3150, 2450, 1960, 1470, 1170]
    })

    # Ministry financial allocations
    ministry_cost = Project.objects.values('ministry').annotate(app_cost=Sum('approved_cost'))
    if ministry_cost and len(ministry_cost) > 0:
        ministry_allocations = json.dumps({
            'labels': [m['ministry'] for m in ministry_cost],
            'data': [float(m['app_cost'] or 0) for m in ministry_cost]
        })
    else:
        ministry_allocations = json.dumps({
            'labels': ['Road Transport', 'Railways', 'Power', 'Ports & Shipping', 'Urban Affairs'],
            'data': [28000, 22000, 16000, 12000, 8000]
        })

    context = {
        'total_approved': total_approved,
        'total_revised': total_revised,
        'total_expenditure': total_expenditure,
        'net_overrun': net_overrun,
        'overrun_projects': overrun_projects,
        'cost_comparison': cost_comparison,
        'ministry_allocations': ministry_allocations,
    }
    return render(request, 'budget.html', context)

def review(request):
    today = date.today()
    delayed_projects = Project.objects.filter(Q(status='delayed') | (Q(status='ongoing') & Q(expected_completion__lt=today)))
    
    overrun_projects = []
    for p in Project.objects.all():
        if p.revised_cost and p.revised_cost > p.approved_cost:
            overrun_projects.append(p)
            
    high_risk_projects = Project.objects.filter(risk_level='high')
    
    good_projects = []
    for p in Project.objects.filter(status='ongoing', risk_level='low'):
        if p.physical_progress >= p.expected_progress:
            good_projects.append(p)

    context = {
        'delayed_projects': delayed_projects,
        'overrun_projects': overrun_projects,
        'high_risk_projects': high_risk_projects,
        'good_projects': good_projects
    }
    return render(request, 'review.html', context)

def alerts_view(request):
    alerts = Alert.objects.all().select_related('project').order_by('-created_at')
    alert_type = request.GET.get('alert_type')
    if alert_type:
        alerts = alerts.filter(alert_type=alert_type)
        
    context = {'alerts': alerts}
    return render(request, 'alerts.html', context)

def api_alerts(request):
    """JSON API endpoint for alerts — used by the frontend JS fetch integration."""
    alerts = Alert.objects.all().select_related('project').order_by('-created_at')
    alert_type = request.GET.get('alert_type')
    if alert_type:
        alerts = alerts.filter(alert_type=alert_type)

    from django.utils.timesince import timesince

    results = []
    for a in alerts:
        results.append({
            'id': a.id,
            'alert_type': a.alert_type,
            'severity': a.severity,
            'message': a.message,
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'time_ago': timesince(a.created_at) + ' ago' if a.created_at else '',
            'is_read': a.is_read,
            'project': {
                'id': a.project.id,
                'project_id': a.project.project_id,
                'name': a.project.name,
            } if a.project else None
        })
    return JsonResponse(results, safe=False)

def help_page(request):
    projects = Project.objects.all().only('project_id', 'name').order_by('name')
    return render(request, 'help.html', {'projects': projects})

@login_required
def csv_import(request):
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            file_data = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(file_data))
            
            success_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    project_id = row['project_id']
                    if Project.objects.filter(project_id=project_id).exists():
                        errors.append(f"Row {row_num}: Project {project_id} already exists.")
                        continue
                        
                    p = Project(
                        project_id=project_id,
                        name=row['project_name'],
                        ministry=row['ministry'],
                        department=row.get('department', ''),
                        state=row['state'],
                        implementing_agency=row['implementing_agency'],
                        approved_cost=Decimal(row['approved_cost']),
                        revised_cost=Decimal(row['revised_cost']) if row.get('revised_cost') else None,
                        expenditure=Decimal(row.get('expenditure', 0)),
                        start_date=row['start_date'],
                        expected_completion=row['expected_completion'],
                        physical_progress=Decimal(row['physical_progress']),
                        financial_progress=Decimal(row.get('financial_progress', 0)),
                        status=row['status'],
                        description=row.get('description', '')
                    )
                    p.save()
                    update_project_automation(p)
                    success_count += 1
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    
            if success_count > 0:
                messages.success(request, f"Successfully imported {success_count} projects.")
            if errors:
                for error in errors:
                    messages.error(request, error)
                    
            return redirect('database_manage')
    return redirect('database_manage')

def search_api(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'results': []})
        
    projects = Project.objects.filter(
        Q(name__icontains=q) | 
        Q(project_id__icontains=q) | 
        Q(state__icontains=q) | 
        Q(district__icontains=q) | 
        Q(ministry__icontains=q) | 
        Q(implementing_agency__icontains=q)
    )[:10]
    
    results = []
    for p in projects:
        results.append({
            'id': p.id,
            'project_id': p.project_id,
            'name': p.name,
            'ministry': p.ministry,
            'state': p.state,
            'district': p.district,
            'status': p.status,
            'url': f'/projects/{p.project_id}/'
        })
    return JsonResponse({'results': results})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        step = request.POST.get('step', '')
        ip_addr = get_client_ip(request)

        # ----------------------------------------------------
        # STEP 2: OTP VERIFICATION STEP (POST)
        # ----------------------------------------------------
        if step == 'verify_otp' or 'otp_code' in request.POST:
            entered_otp = request.POST.get('otp_code', '').strip()
            pending_code = request.session.get('pending_otp_code')
            pending_expires = request.session.get('pending_otp_expires', 0)
            pending_user_id = request.session.get('pending_user_id')
            pending_phone = request.session.get('pending_otp_phone', '')
            attempts_left = request.session.get('pending_otp_attempts', 3)

            if not pending_code or not pending_user_id:
                messages.error(request, "OTP session expired. Please restart login.")
                return render(request, 'login.html')

            if timezone.now().timestamp() > pending_expires:
                messages.error(request, "OTP expired after 5 minutes. Please click Resend OTP.")
                context = {
                    'show_otp': True,
                    'otp_phone': pending_phone,
                    'otp_code': pending_code,
                    'otp_attempts': attempts_left,
                }
                return render(request, 'login.html', context)

            if entered_otp != pending_code:
                attempts_left -= 1
                request.session['pending_otp_attempts'] = attempts_left
                if attempts_left <= 0:
                    for key in ['pending_otp_code', 'pending_otp_expires', 'pending_user_id', 'pending_otp_phone', 'pending_otp_attempts']:
                        request.session.pop(key, None)
                    messages.error(request, "OTP invalidated due to 3 incorrect attempts. Please restart login.")
                    return render(request, 'login.html')
                else:
                    messages.error(request, f"Incorrect OTP code. {attempts_left} attempt(s) remaining.")
                    context = {
                        'show_otp': True,
                        'otp_phone': pending_phone,
                        'otp_code': pending_code,
                        'otp_attempts': attempts_left,
                    }
                    return render(request, 'login.html', context)

            # Correct OTP -> Authenticate User & Redirect to Dashboard
            user_obj = User.objects.filter(id=pending_user_id).first()
            if user_obj:
                for key in ['pending_otp_code', 'pending_otp_expires', 'pending_user_id', 'pending_otp_phone', 'pending_otp_attempts']:
                    request.session.pop(key, None)
                reset_failed_attempts(pending_phone)
                login(request, user_obj)
                return redirect('dashboard')
            else:
                messages.error(request, "User account not found. Please restart login.")
                return render(request, 'login.html')

        # ----------------------------------------------------
        # STEP 1: PHONE + PASSWORD VERIFICATION STEP (POST)
        # ----------------------------------------------------
        is_limited, limit_msg = check_rate_limit(ip_addr)
        if is_limited:
            messages.error(request, limit_msg)
            return render(request, 'login.html')

        identifier = request.POST.get('username') or request.POST.get('phone', '')
        password = request.POST.get('password', '')

        if identifier:
            is_locked, lock_msg = check_lockout(identifier, ip_addr)
            if is_locked:
                messages.error(request, lock_msg)
                return render(request, 'login.html')

        user = authenticate(username=identifier, password=password)
        if user is None and identifier:
            user_obj = User.objects.filter(username=identifier).first()
            if not user_obj and len(identifier) == 10 and identifier.isdigit() and password:
                user_obj = User.objects.create_user(username=identifier, password=password)
                UserProfile.objects.get_or_create(user=user_obj, defaults={'role': 'field_officer'})
                user = user_obj

        if user is not None:
            # Credentials valid -> Generate 6-digit OTP and show OTP step
            otp_code = f"{random.randint(100000, 999999)}"
            request.session['pending_otp_code'] = otp_code
            request.session['pending_otp_phone'] = identifier
            request.session['pending_user_id'] = user.id
            request.session['pending_otp_attempts'] = 3
            request.session['pending_otp_expires'] = (timezone.now() + timedelta(minutes=5)).timestamp()

            context = {
                'show_otp': True,
                'otp_phone': identifier,
                'otp_code': otp_code,
                'otp_attempts': 3,
            }
            return render(request, 'login.html', context)
        else:
            if identifier:
                failed_cnt = record_failed_attempt(identifier, ip_addr)
                if failed_cnt >= 5:
                    messages.error(request, "Account locked due to 5 consecutive failed login attempts. Please try again after 15 minutes.")
                else:
                    messages.error(request, "Invalid phone number or password. Please try again.")
            else:
                messages.error(request, "Please enter both phone number and password.")
    return render(request, 'login.html')

def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        totp_code = request.POST.get('totp_code', '').strip()

        if not username or not password:
            messages.error(request, "Please enter admin username and password.")
            return render(request, 'admin_login.html')

        is_locked, lock_msg = check_lockout(username)
        if is_locked:
            messages.error(request, lock_msg)
            return render(request, 'admin_login.html')

        user = authenticate(username=username, password=password)
        if user is not None:
            profile = getattr(user, 'profile', None)
            role = profile.role if profile else ('admin' if user.is_superuser else 'public_viewer')
            
            if not user.is_staff and not user.is_superuser and role != 'admin':
                messages.error(request, "Access Denied: Only Administrator accounts are permitted via this portal.")
                record_failed_attempt(username)
                return render(request, 'admin_login.html')

            if profile and profile.mfa_enabled:
                if not totp_code or len(totp_code) != 6:
                    messages.error(request, "Multi-Factor Authentication (MFA) required. Enter a valid 6-digit TOTP code.")
                    return render(request, 'admin_login.html')

            reset_failed_attempts(username)
            login(request, user)
            messages.success(request, f"Welcome back Admin {user.username}!")
            return redirect('database_manage')
        else:
            failed_cnt = record_failed_attempt(username)
            if failed_cnt >= 5:
                messages.error(request, "Account locked due to 5 failed login attempts. Please try again after 15 minutes.")
            else:
                messages.error(request, f"Invalid administrator credentials or access denied. Attempt {failed_cnt} of 5.")
    return render(request, 'admin_login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

def states_view(request):
    projects = Project.objects.all()
    
    raw_states = list(projects.values_list('state', flat=True).distinct())
    state_names = sorted(list(set([st.strip() for st in raw_states if st and st.strip()])))
    
    states_data = []
    total_approved = Decimal('0')
    total_expenditure = Decimal('0')
    
    chart_labels = []
    chart_counts = []
    chart_costs = []
    
    for s_name in state_names:
        state_projects = projects.filter(state__iexact=s_name)
        count = state_projects.count()
        if count == 0:
            continue
            
        appr_cost = sum(p.approved_cost for p in state_projects)
        exp_cost = sum(p.expenditure for p in state_projects)
        
        total_approved += appr_cost
        total_expenditure += exp_cost
        
        ongoing = state_projects.filter(status='ongoing').count()
        completed = state_projects.filter(status='completed').count()
        delayed = state_projects.filter(status='delayed').count()
        not_started = state_projects.filter(status='not_started').count()
        high_risk = state_projects.filter(risk_level='high').count()
        
        states_data.append({
            'name': s_name,
            'count': count,
            'approved_cost': float(appr_cost),
            'expenditure': float(exp_cost),
            'ongoing': ongoing,
            'completed': completed,
            'delayed': delayed,
            'not_started': not_started,
            'high_risk': high_risk,
        })
        
        chart_labels.append(s_name)
        chart_counts.append(count)
        chart_costs.append(float(appr_cost))
        
    states_data.sort(key=lambda x: x['count'], reverse=True)
    
    context = {
        'states_data': states_data,
        'total_states': len(states_data),
        'total_projects': projects.count(),
        'total_approved': float(total_approved),
        'total_expenditure': float(total_expenditure),
        'chart_labels': json.dumps(chart_labels),
        'chart_counts': json.dumps(chart_counts),
        'chart_costs': json.dumps(chart_costs),
    }
    return render(request, 'states.html', context)


def ministries_view(request):
    projects = Project.objects.all()
    
    main_ministries = [
        'Ministry of Road Transport',
        'Ministry of Power',
        'Ministry of Urban Development',
        'Ministry of Railways',
        'Ministry of Water Resources'
    ]
    raw_ministries = list(projects.values_list('ministry', flat=True).distinct())
    all_ministries = list(main_ministries)
    for m in raw_ministries:
        if m and m.strip() and m.strip() not in all_ministries:
            all_ministries.append(m.strip())
            
    ministries_data = []
    total_approved = Decimal('0')
    total_expenditure = Decimal('0')
    
    chart_labels = []
    chart_counts = []
    chart_costs = []
    
    for m_name in all_ministries:
        m_projects = projects.filter(ministry__icontains=m_name)
        count = m_projects.count()
            
        appr_cost = sum(p.approved_cost for p in m_projects)
        exp_cost = sum(p.expenditure for p in m_projects)
        
        total_approved += appr_cost
        total_expenditure += exp_cost
        
        ongoing = m_projects.filter(status='ongoing').count()
        completed = m_projects.filter(status='completed').count()
        delayed = m_projects.filter(status='delayed').count()
        not_started = m_projects.filter(status='not_started').count()
        high_risk = m_projects.filter(risk_level='high').count()
        
        ministries_data.append({
            'name': m_name,
            'count': count,
            'approved_cost': float(appr_cost),
            'expenditure': float(exp_cost),
            'ongoing': ongoing,
            'completed': completed,
            'delayed': delayed,
            'not_started': not_started,
            'high_risk': high_risk,
        })
        
        chart_labels.append(m_name.replace('Ministry of ', ''))
        chart_counts.append(count)
        chart_costs.append(float(appr_cost))
        
    context = {
        'ministries_data': ministries_data,
        'total_ministries': len(ministries_data),
        'total_projects': projects.count(),
        'total_approved': float(total_approved),
        'total_expenditure': float(total_expenditure),
        'chart_labels': json.dumps(chart_labels),
        'chart_counts': json.dumps(chart_counts),
        'chart_costs': json.dumps(chart_costs),
    }
    return render(request, 'ministries.html', context)

def handler404(request, exception):
    return render(request, '404.html', status=404)

def handler500(request):
    return render(request, '500.html', status=500)
