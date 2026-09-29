from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from monitoring.models import Project, Milestone, Alert
from monitoring.automation import update_project_automation
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seeds the database with 40 realistic infrastructure projects across Indian states.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding.')

    def handle(self, *args, **kwargs):
        if kwargs['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Alert.objects.all().delete()
            Milestone.objects.all().delete()
            Project.objects.all().delete()
            User.objects.filter(username='admin').delete()
            self.stdout.write(self.style.SUCCESS('Data cleared.'))

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Superuser "admin" created.'))

        projects_data = [
            # West Bengal (10)
            {'id': 'PROJ-001', 'name': 'Kolkata Metro East-West Line (Phase II)', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'Kolkata', 'agency': 'KMRCL', 'cost': 3150, 'prog': 88, 'status': 'ongoing', 'start': '2018-03-15', 'end': '2027-12-31', 'revised': None, 'exp': 2772, 'is_new': True},
            {'id': 'PROJ-002', 'name': 'Kolkata-Siliguri Economic Corridor (NH-12)', 'ministry': 'Ministry of Road Transport', 'state': 'West Bengal', 'district': 'North 24 Parganas', 'agency': 'NHAI', 'cost': 2600, 'prog': 48, 'status': 'ongoing', 'start': '2021-01-10', 'end': '2028-12-31', 'revised': None, 'exp': 1248, 'is_new': True},
            {'id': 'PROJ-003', 'name': 'Syama Prasad Mookerjee Port Modernization', 'ministry': 'Ministry of Shipping', 'state': 'West Bengal', 'district': 'Kolkata', 'agency': 'SMPK', 'cost': 1500, 'prog': 100, 'status': 'completed', 'start': '2019-01-10', 'end': '2024-01-15', 'revised': 1650, 'exp': 1650},
            {'id': 'PROJ-004', 'name': 'Teesta Barrage Irrigation Project', 'ministry': 'Ministry of Water Resources', 'state': 'West Bengal', 'district': 'Jalpaiguri', 'agency': 'Irrigation & Waterways Dept', 'cost': 1100, 'prog': 60, 'status': 'ongoing', 'start': '2020-03-15', 'end': '2027-11-30', 'revised': None, 'exp': 660},
            {'id': 'PROJ-005', 'name': 'Kolkata Metro Purple Line (Joka-Esplanade)', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'South 24 Parganas', 'agency': 'RVNL', 'cost': 1300, 'prog': 55, 'status': 'delayed', 'start': '2019-07-01', 'end': '2024-03-31', 'revised': 1500, 'exp': 845},
            {'id': 'PROJ-006', 'name': 'Howrah Station Redevelopment Hub', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'Howrah', 'agency': 'RLDA', 'cost': 950, 'prog': 25, 'status': 'ongoing', 'start': '2023-02-01', 'end': '2028-12-31', 'revised': None, 'exp': 285},
            {'id': 'PROJ-007', 'name': 'Purulia Pumped Storage Solar Grid', 'ministry': 'Ministry of Power', 'state': 'West Bengal', 'district': 'Purulia', 'agency': 'WBSEDCL', 'cost': 1200, 'prog': 100, 'status': 'completed', 'start': '2020-01-15', 'end': '2024-03-31', 'revised': None, 'exp': 1200},
            {'id': 'PROJ-008', 'name': 'Durgapur Steel City Power Plant Modernization', 'ministry': 'Ministry of Power', 'state': 'West Bengal', 'district': 'Paschim Bardhaman', 'agency': 'DVC', 'cost': 1050, 'prog': 50, 'status': 'delayed', 'start': '2020-01-10', 'end': '2024-02-28', 'revised': 1200, 'exp': 630},
            {'id': 'PROJ-009', 'name': 'Bagdogra Airport New Integrated Terminal', 'ministry': 'Ministry of Civil Aviation', 'state': 'West Bengal', 'district': 'Darjeeling', 'agency': 'AAI', 'cost': 750, 'prog': 30, 'status': 'ongoing', 'start': '2023-03-01', 'end': '2028-06-30', 'revised': None, 'exp': 225},
            {'id': 'PROJ-010', 'name': 'Dankuni Freight Logistics Park Hub', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'Hooghly', 'agency': 'DFCCIL', 'cost': 600, 'prog': 0, 'status': 'not_started', 'start': '2024-05-01', 'end': '2028-12-31', 'revised': None, 'exp': 0},

            # Maharashtra (4)
            {'id': 'PROJ-011', 'name': 'Mumbai Trans Harbour Link (MTHL)', 'ministry': 'Ministry of Road Transport', 'state': 'Maharashtra', 'district': 'Mumbai', 'agency': 'MMRDA', 'cost': 2800, 'prog': 95, 'status': 'ongoing', 'start': '2018-04-01', 'end': '2027-06-30', 'revised': None, 'exp': 2660},
            {'id': 'PROJ-012', 'name': 'Pune Metro Rail Line 3', 'ministry': 'Ministry of Railways', 'state': 'Maharashtra', 'district': 'Pune', 'agency': 'PMRDA', 'cost': 1700, 'prog': 65, 'status': 'ongoing', 'start': '2020-11-01', 'end': '2027-03-31', 'revised': None, 'exp': 1105},
            {'id': 'PROJ-013', 'name': 'Nagpur Smart City Water Grid', 'ministry': 'Ministry of Urban Development', 'state': 'Maharashtra', 'district': 'Nagpur', 'agency': 'NMC', 'cost': 700, 'prog': 100, 'status': 'completed', 'start': '2019-06-01', 'end': '2023-12-31', 'revised': None, 'exp': 700},
            {'id': 'PROJ-014', 'name': 'Jawaharlal Nehru Port Terminal Extension', 'ministry': 'Ministry of Shipping', 'state': 'Maharashtra', 'district': 'Navi Mumbai', 'agency': 'JNPA', 'cost': 1400, 'prog': 45, 'status': 'delayed', 'start': '2020-02-15', 'end': '2024-01-31', 'revised': 1550, 'exp': 770},

            # Karnataka (4)
            {'id': 'PROJ-015', 'name': 'Bengaluru Metro Phase 2B (Airport Line)', 'ministry': 'Ministry of Railways', 'state': 'Karnataka', 'district': 'Bengaluru Urban', 'agency': 'BMRCL', 'cost': 2200, 'prog': 60, 'status': 'ongoing', 'start': '2021-02-01', 'end': '2027-08-31', 'revised': None, 'exp': 1320},
            {'id': 'PROJ-016', 'name': 'Bengaluru Suburban Rail Project', 'ministry': 'Ministry of Railways', 'state': 'Karnataka', 'district': 'Bengaluru Rural', 'agency': 'K-RIDE', 'cost': 1500, 'prog': 35, 'status': 'delayed', 'start': '2021-09-01', 'end': '2024-04-30', 'revised': 1650, 'exp': 525},
            {'id': 'PROJ-017', 'name': 'Mysuru-Madikeri Economic Corridor', 'ministry': 'Ministry of Road Transport', 'state': 'Karnataka', 'district': 'Mysuru', 'agency': 'NHAI', 'cost': 850, 'prog': 75, 'status': 'ongoing', 'start': '2021-05-15', 'end': '2027-10-31', 'revised': None, 'exp': 637.5},
            {'id': 'PROJ-018', 'name': 'Pavagada Solar Park Expansion', 'ministry': 'Ministry of Power', 'state': 'Karnataka', 'district': 'Tumakuru', 'agency': 'KREDL', 'cost': 1000, 'prog': 100, 'status': 'completed', 'start': '2020-04-01', 'end': '2024-02-15', 'revised': None, 'exp': 1000},

            # Uttar Pradesh (4)
            {'id': 'PROJ-019', 'name': 'Noida International Airport (Jewar Phase 1)', 'ministry': 'Ministry of Civil Aviation', 'state': 'Uttar Pradesh', 'district': 'Gautam Buddha Nagar', 'agency': 'YIAPL', 'cost': 2100, 'prog': 85, 'status': 'ongoing', 'start': '2021-06-01', 'end': '2027-09-30', 'revised': None, 'exp': 1785},
            {'id': 'PROJ-020', 'name': 'Ganga Expressway Phase 1', 'ministry': 'Ministry of Road Transport', 'state': 'Uttar Pradesh', 'district': 'Meerut', 'agency': 'UPEIDA', 'cost': 2500, 'prog': 70, 'status': 'ongoing', 'start': '2022-01-10', 'end': '2027-05-31', 'revised': None, 'exp': 1750},
            {'id': 'PROJ-021', 'name': 'Lucknow Metro Phase 1B Extension', 'ministry': 'Ministry of Railways', 'state': 'Uttar Pradesh', 'district': 'Lucknow', 'agency': 'UPMRC', 'cost': 1000, 'prog': 40, 'status': 'delayed', 'start': '2020-08-01', 'end': '2024-05-31', 'revised': 1150, 'exp': 480},
            {'id': 'PROJ-022', 'name': 'Varanasi Multi-Modal Freight Terminal', 'ministry': 'Ministry of Shipping', 'state': 'Uttar Pradesh', 'district': 'Varanasi', 'agency': 'IWAI', 'cost': 600, 'prog': 92, 'status': 'ongoing', 'start': '2020-03-01', 'end': '2027-03-31', 'revised': None, 'exp': 552},

            # Gujarat (3)
            {'id': 'PROJ-023', 'name': 'Ahmedabad-Gandhinagar Metro Phase 2', 'ministry': 'Ministry of Railways', 'state': 'Gujarat', 'district': 'Ahmedabad', 'agency': 'GMRC', 'cost': 1300, 'prog': 80, 'status': 'ongoing', 'start': '2021-03-15', 'end': '2027-08-31', 'revised': None, 'exp': 1040},
            {'id': 'PROJ-024', 'name': 'Dholera Special Investment Region Solar Park', 'ministry': 'Ministry of Power', 'state': 'Gujarat', 'district': 'Ahmedabad', 'agency': 'GPCL', 'cost': 1100, 'prog': 45, 'status': 'delayed', 'start': '2021-07-01', 'end': '2024-06-30', 'revised': 1250, 'exp': 550},
            {'id': 'PROJ-025', 'name': 'Surat Bullet Train Terminal Complex', 'ministry': 'Ministry of Railways', 'state': 'Gujarat', 'district': 'Surat', 'agency': 'NHSRCL', 'cost': 900, 'prog': 55, 'status': 'ongoing', 'start': '2022-04-01', 'end': '2027-12-31', 'revised': None, 'exp': 495},

            # Tamil Nadu (3)
            {'id': 'PROJ-026', 'name': 'Chennai Metro Rail Phase 2 Corridor 3', 'ministry': 'Ministry of Railways', 'state': 'Tamil Nadu', 'district': 'Chennai', 'agency': 'CMRL', 'cost': 1900, 'prog': 52, 'status': 'ongoing', 'start': '2021-08-01', 'end': '2027-11-30', 'revised': None, 'exp': 988},
            {'id': 'PROJ-027', 'name': 'Koodankulam Nuclear Power Unit 3', 'ministry': 'Ministry of Power', 'state': 'Tamil Nadu', 'district': 'Tirunelveli', 'agency': 'NPCIL', 'cost': 1650, 'prog': 65, 'status': 'delayed', 'start': '2019-10-01', 'end': '2024-03-31', 'revised': 1850, 'exp': 1155},
            {'id': 'PROJ-028', 'name': 'Coimbatore Bypass Expressway', 'ministry': 'Ministry of Road Transport', 'state': 'Tamil Nadu', 'district': 'Coimbatore', 'agency': 'NHAI', 'cost': 500, 'prog': 0, 'status': 'not_started', 'start': '2024-06-01', 'end': '2028-05-31', 'revised': None, 'exp': 0},

            # Odisha (3)
            {'id': 'PROJ-029', 'name': 'Paradeep Port Outer Harbour Terminal', 'ministry': 'Ministry of Shipping', 'state': 'Odisha', 'district': 'Jagatsinghpur', 'agency': 'PPA', 'cost': 950, 'prog': 82, 'status': 'ongoing', 'start': '2020-05-10', 'end': '2027-07-31', 'revised': None, 'exp': 779},
            {'id': 'PROJ-030', 'name': 'Bhubaneswar Smart City Command Centre', 'ministry': 'Ministry of Urban Development', 'state': 'Odisha', 'district': 'Khurda', 'agency': 'BSCL', 'cost': 350, 'prog': 100, 'status': 'completed', 'start': '2020-01-10', 'end': '2023-10-31', 'revised': None, 'exp': 350},
            {'id': 'PROJ-031', 'name': 'Mahanadi Basin Flood Control & Dam Safety', 'ministry': 'Ministry of Water Resources', 'state': 'Odisha', 'district': 'Cuttack', 'agency': 'OWR', 'cost': 650, 'prog': 42, 'status': 'delayed', 'start': '2021-04-01', 'end': '2024-04-30', 'revised': 750, 'exp': 325},

            # Rajasthan (3)
            {'id': 'PROJ-032', 'name': 'Bhadla Solar Park Phase 4 Expansion', 'ministry': 'Ministry of Power', 'state': 'Rajasthan', 'district': 'Jodhpur', 'agency': 'RREC', 'cost': 1050, 'prog': 88, 'status': 'ongoing', 'start': '2021-01-15', 'end': '2027-04-30', 'revised': None, 'exp': 924},
            {'id': 'PROJ-033', 'name': 'Jaipur Ring Road Expressway Phase 2', 'ministry': 'Ministry of Road Transport', 'state': 'Rajasthan', 'district': 'Jaipur', 'agency': 'NHAI', 'cost': 750, 'prog': 58, 'status': 'ongoing', 'start': '2022-02-01', 'end': '2027-01-31', 'revised': None, 'exp': 435},
            {'id': 'PROJ-034', 'name': 'Jodhpur Water Distribution Augmentation', 'ministry': 'Ministry of Water Resources', 'state': 'Rajasthan', 'district': 'Jodhpur', 'agency': 'PHED Rajasthan', 'cost': 400, 'prog': 100, 'status': 'completed', 'start': '2020-07-01', 'end': '2024-02-28', 'revised': None, 'exp': 400},

            # Telangana (3)
            {'id': 'PROJ-035', 'name': 'Hyderabad Regional Ring Road (Northern Part)', 'ministry': 'Ministry of Road Transport', 'state': 'Telangana', 'district': 'Hyderabad', 'agency': 'NHAI', 'cost': 1350, 'prog': 38, 'status': 'delayed', 'start': '2021-09-15', 'end': '2024-05-31', 'revised': 1500, 'exp': 513},
            {'id': 'PROJ-036', 'name': 'Kaleshwaram Lift Irrigation Grid Phase 3', 'ministry': 'Ministry of Water Resources', 'state': 'Telangana', 'district': 'Karimnagar', 'agency': 'TSIIC', 'cost': 1200, 'prog': 75, 'status': 'ongoing', 'start': '2020-10-01', 'end': '2027-09-30', 'revised': None, 'exp': 900},
            {'id': 'PROJ-037', 'name': 'Hyderabad Airport Express Metro Line', 'ministry': 'Ministry of Railways', 'state': 'Telangana', 'district': 'Rangareddy', 'agency': 'HAML', 'cost': 750, 'prog': 20, 'status': 'ongoing', 'start': '2023-04-01', 'end': '2028-08-31', 'revised': None, 'exp': 150},

            # Andhra Pradesh (3)
            {'id': 'PROJ-038', 'name': 'Visakhapatnam Deep Water Port Expansion', 'ministry': 'Ministry of Shipping', 'state': 'Andhra Pradesh', 'district': 'Visakhapatnam', 'agency': 'VPA', 'cost': 850, 'prog': 65, 'status': 'ongoing', 'start': '2021-05-01', 'end': '2027-12-31', 'revised': None, 'exp': 552.5},
            {'id': 'PROJ-039', 'name': 'Polavaram Irrigation Hydro Complex', 'ministry': 'Ministry of Water Resources', 'state': 'Andhra Pradesh', 'district': 'Eluru', 'agency': 'PPA', 'cost': 1250, 'prog': 48, 'status': 'delayed', 'start': '2019-12-01', 'end': '2024-02-29', 'revised': 1400, 'exp': 600},
            {'id': 'PROJ-040', 'name': 'Bhogapuram Green International Airport', 'ministry': 'Ministry of Civil Aviation', 'state': 'Andhra Pradesh', 'district': 'Vizianagaram', 'agency': 'GMRAP', 'cost': 550, 'prog': 0, 'status': 'not_started', 'start': '2024-07-01', 'end': '2028-10-31', 'revised': None, 'exp': 0}
        ]

        self.stdout.write(self.style.WARNING(f'Creating {len(projects_data)} realistic infrastructure projects...'))

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=45)

        for p_data in projects_data:
            financial_progress = (p_data['exp'] / p_data['cost']) * 100 if p_data['cost'] else 0
            
            project, created = Project.objects.update_or_create(
                project_id=p_data['id'],
                defaults={
                    'name': p_data['name'],
                    'ministry': p_data['ministry'],
                    'state': p_data['state'],
                    'district': p_data.get('district', ''),
                    'implementing_agency': p_data['agency'],
                    'approved_cost': Decimal(str(p_data['cost'])),
                    'revised_cost': Decimal(str(p_data['revised'])) if p_data['revised'] else None,
                    'expenditure': Decimal(str(p_data['exp'])),
                    'start_date': date.fromisoformat(p_data['start']),
                    'expected_completion': date.fromisoformat(p_data['end']),
                    'physical_progress': Decimal(str(p_data['prog'])),
                    'financial_progress': Decimal(str(round(financial_progress, 2))),
                    'status': p_data['status'],
                    'description': f"Infrastructure project: {p_data['name']} in {p_data['state']}."
                }
            )

            # Control created_at so exactly 2 projects are 'new_added' (within 30 days)
            if p_data.get('is_new'):
                Project.objects.filter(id=project.id).update(created_at=now - timedelta(days=5))
            else:
                Project.objects.filter(id=project.id).update(created_at=thirty_days_ago)

            project.milestones.all().delete()
            
            milestones = ['Planning & DPR', 'Land Acquisition', 'Tender Process', 'Construction Phase I', '50% Construction', 'Final Completion']
            for idx, m_name in enumerate(milestones):
                m_status = 'pending'
                if project.physical_progress >= 100:
                    m_status = 'completed'
                elif project.physical_progress > idx * 20:
                    m_status = 'completed' if project.physical_progress > (idx+1)*20 else 'in_progress'
                
                Milestone.objects.create(
                    project=project,
                    name=m_name,
                    order=idx,
                    status=m_status
                )
            
            project.refresh_from_db()
            update_project_automation(project)

        # Set exactly 15 projects as high risk
        all_projs = list(Project.objects.order_by('id'))
        # Mark 10 delayed projects + 5 additional projects as high risk
        high_risk_indices = [4, 7, 13, 15, 20, 23, 26, 30, 34, 38, 5, 8, 14, 18, 24] # 15 projects total
        for idx, proj in enumerate(all_projs):
            if idx in high_risk_indices:
                proj.risk_level = 'high'
            else:
                proj.risk_level = 'low' if proj.status in ['completed', 'ongoing'] else 'medium'
            proj.save(update_fields=['risk_level'])

        self.stdout.write(self.style.SUCCESS('Successfully seeded 40 infrastructure projects.'))
