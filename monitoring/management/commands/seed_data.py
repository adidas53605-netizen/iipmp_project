from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from monitoring.models import Project, Milestone, Alert
from monitoring.automation import update_project_automation
from decimal import Decimal
from datetime import date

class Command(BaseCommand):
    help = 'Seeds the database with 54 realistic infrastructure projects with diverse states and statuses.'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding.')

    def handle(self, *args, **kwargs):
        if kwargs['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Project.objects.all().delete()
            User.objects.filter(username='admin').delete()
            self.stdout.write(self.style.SUCCESS('Data cleared.'))

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Superuser "admin" created.'))

        projects_data = [
            {'id': 'PROJ-001', 'name': 'Kolkata Metro East-West Line (Phase II)', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'Kolkata', 'agency': 'KMRCL', 'cost': 8575, 'prog': 88, 'status': 'ongoing', 'start': '2018-03-15', 'end': '2025-12-31', 'revised': None, 'exp': 7546},
            {'id': 'PROJ-002', 'name': 'Bullet Train Corridor (Ahmedabad-Mumbai)', 'ministry': 'Ministry of Railways', 'state': 'Gujarat', 'district': 'Ahmedabad', 'agency': 'NHSRCL', 'cost': 110000, 'prog': 42, 'status': 'ongoing', 'start': '2019-10-01', 'end': '2026-06-30', 'revised': 120000, 'exp': 46200},
            {'id': 'PROJ-003', 'name': 'Kolkata-Siliguri Economic Corridor (NH-12)', 'ministry': 'Ministry of Road Transport', 'state': 'West Bengal', 'district': 'North 24 Parganas', 'agency': 'NHAI', 'cost': 14500, 'prog': 48, 'status': 'ongoing', 'start': '2021-01-10', 'end': '2026-12-31', 'revised': None, 'exp': 6960},
            {'id': 'PROJ-004', 'name': 'Mumbai Trans Harbour Link', 'ministry': 'Ministry of Road Transport', 'state': 'Maharashtra', 'district': 'Mumbai', 'agency': 'MMRDA', 'cost': 18000, 'prog': 100, 'status': 'completed', 'start': '2019-03-10', 'end': '2024-01-12', 'revised': 20000, 'exp': 20000},
            {'id': 'PROJ-005', 'name': 'Polavaram Irrigation Project', 'ministry': 'Ministry of Water Resources', 'state': 'Andhra Pradesh', 'district': 'West Godavari', 'agency': 'Polavaram Project Authority', 'cost': 55000, 'prog': 72, 'status': 'delayed', 'start': '2019-01-01', 'end': '2023-12-31', 'revised': 65000, 'exp': 39600},
            {'id': 'PROJ-006', 'name': 'Chennai Metro Rail Phase II', 'ministry': 'Ministry of Urban Development', 'state': 'Tamil Nadu', 'district': 'Chennai', 'agency': 'CMRL', 'cost': 63000, 'prog': 35, 'status': 'ongoing', 'start': '2021-04-10', 'end': '2027-03-31', 'revised': None, 'exp': 22050},
            {'id': 'PROJ-007', 'name': 'Ganga Expressway', 'ministry': 'Ministry of Road Transport', 'state': 'Uttar Pradesh', 'district': 'Lucknow', 'agency': 'UPEIDA', 'cost': 36200, 'prog': 55, 'status': 'ongoing', 'start': '2022-02-01', 'end': '2025-08-31', 'revised': None, 'exp': 19910},
            {'id': 'PROJ-008', 'name': 'Syama Prasad Mookerjee Port Modernization', 'ministry': 'Ministry of Shipping', 'state': 'West Bengal', 'district': 'Kolkata', 'agency': 'SMPK', 'cost': 4200, 'prog': 100, 'status': 'completed', 'start': '2019-01-10', 'end': '2024-01-15', 'revised': 4500, 'exp': 4500},
            {'id': 'PROJ-009', 'name': 'Zojila Tunnel Project', 'ministry': 'Ministry of Road Transport', 'state': 'Jammu & Kashmir', 'district': 'Kargil', 'agency': 'NHIDCL', 'cost': 6800, 'prog': 28, 'status': 'delayed', 'start': '2020-10-15', 'end': '2024-12-31', 'revised': 8000, 'exp': 1904},
            {'id': 'PROJ-010', 'name': 'Bengaluru Suburban Rail', 'ministry': 'Ministry of Railways', 'state': 'Karnataka', 'district': 'Bengaluru Urban', 'agency': 'K-RIDE', 'cost': 15700, 'prog': 15, 'status': 'ongoing', 'start': '2022-10-01', 'end': '2028-12-31', 'revised': None, 'exp': 2355},
            {'id': 'PROJ-011', 'name': 'Teesta Barrage Irrigation Project', 'ministry': 'Ministry of Water Resources', 'state': 'West Bengal', 'district': 'Jalpaiguri', 'agency': 'Irrigation & Waterways Dept', 'cost': 6200, 'prog': 58, 'status': 'ongoing', 'start': '2020-03-15', 'end': '2025-11-30', 'revised': None, 'exp': 3596},
            {'id': 'PROJ-012', 'name': 'Kolkata Metro Purple Line (Joka-Esplanade)', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'South 24 Parganas', 'agency': 'RVNL', 'cost': 2618, 'prog': 52, 'status': 'delayed', 'start': '2019-07-01', 'end': '2024-10-31', 'revised': 3100, 'exp': 1361},
            {'id': 'PROJ-013', 'name': 'Kolkata Metro Orange Line (Kavi Subhash-Biman Bandar)', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'North 24 Parganas', 'agency': 'RVNL', 'cost': 4680, 'prog': 70, 'status': 'ongoing', 'start': '2019-11-01', 'end': '2025-08-31', 'revised': None, 'exp': 3276},
            {'id': 'PROJ-014', 'name': 'NH-17 Widening & Bypass Corridor (Sevoke-Hashimara)', 'ministry': 'Ministry of Road Transport', 'state': 'West Bengal', 'district': 'Darjeeling', 'agency': 'PWD West Bengal', 'cost': 3500, 'prog': 65, 'status': 'ongoing', 'start': '2020-06-15', 'end': '2025-07-31', 'revised': None, 'exp': 2275},
            {'id': 'PROJ-015', 'name': 'Howrah Station Redevelopment & World Class Hub', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'Howrah', 'agency': 'RLDA', 'cost': 2800, 'prog': 15, 'status': 'ongoing', 'start': '2023-02-01', 'end': '2027-12-31', 'revised': None, 'exp': 420},
            {'id': 'PROJ-016', 'name': 'Haldia Petrochemical Zone Deep Water Jetty', 'ministry': 'Ministry of Shipping', 'state': 'West Bengal', 'district': 'Purba Medinipur', 'agency': 'SMPK', 'cost': 2300, 'prog': 82, 'status': 'ongoing', 'start': '2020-05-10', 'end': '2025-04-30', 'revised': None, 'exp': 1886},
            {'id': 'PROJ-017', 'name': 'Smart City Mission - Varanasi', 'ministry': 'Ministry of Urban Development', 'state': 'Uttar Pradesh', 'district': 'Varanasi', 'agency': 'Varanasi Smart City SPV', 'cost': 3000, 'prog': 85, 'status': 'ongoing', 'start': '2020-01-01', 'end': '2024-12-31', 'revised': None, 'exp': 2550},
            {'id': 'PROJ-018', 'name': 'SSKM Super Specialty Hospital Block Expansion', 'ministry': 'Ministry of Health', 'state': 'West Bengal', 'district': 'Kolkata', 'agency': 'PWD West Bengal', 'cost': 850, 'prog': 100, 'status': 'completed', 'start': '2019-08-01', 'end': '2023-11-30', 'revised': 920, 'exp': 920},
            {'id': 'PROJ-019', 'name': 'Purulia Pumped Storage Solar Grid', 'ministry': 'Ministry of Power', 'state': 'West Bengal', 'district': 'Purulia', 'agency': 'WBSEDCL', 'cost': 4500, 'prog': 100, 'status': 'completed', 'start': '2020-01-15', 'end': '2024-03-31', 'revised': None, 'exp': 4500},
            {'id': 'PROJ-020', 'name': 'Digital India Data Centre - Hyderabad', 'ministry': 'Ministry of Electronics & IT', 'state': 'Telangana', 'district': 'Hyderabad', 'agency': 'NIC', 'cost': 2100, 'prog': 0, 'status': 'not_started', 'start': '2024-08-01', 'end': '2026-06-30', 'revised': None, 'exp': 0},
            {'id': 'PROJ-021', 'name': 'Asansol-Durgapur Expressway Extension (NH-19)', 'ministry': 'Ministry of Road Transport', 'state': 'West Bengal', 'district': 'Paschim Bardhaman', 'agency': 'NHAI', 'cost': 3900, 'prog': 75, 'status': 'ongoing', 'start': '2020-04-01', 'end': '2025-06-30', 'revised': None, 'exp': 2925},
            {'id': 'PROJ-022', 'name': 'Siliguri Ring Road & Elevated Corridor', 'ministry': 'Ministry of Road Transport', 'state': 'West Bengal', 'district': 'Darjeeling', 'agency': 'PWD West Bengal', 'cost': 2400, 'prog': 30, 'status': 'ongoing', 'start': '2022-03-15', 'end': '2026-09-30', 'revised': None, 'exp': 720},
            {'id': 'PROJ-023', 'name': 'Malda Medical College Infrastructure Augmentation', 'ministry': 'Ministry of Health', 'state': 'West Bengal', 'district': 'Malda', 'agency': 'WBMED', 'cost': 650, 'prog': 90, 'status': 'ongoing', 'start': '2020-09-01', 'end': '2025-03-31', 'revised': None, 'exp': 585},
            {'id': 'PROJ-024', 'name': 'Kharagpur Industrial Freight Rail Hub', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'Paschim Medinipur', 'agency': 'South Eastern Railway', 'cost': 1850, 'prog': 40, 'status': 'ongoing', 'start': '2021-11-10', 'end': '2026-04-30', 'revised': None, 'exp': 740},
            {'id': 'PROJ-025', 'name': 'Sundarbans Coastal Protection Embankment', 'ministry': 'Ministry of Water Resources', 'state': 'West Bengal', 'district': 'South 24 Parganas', 'agency': 'Irrigation & Waterways Dept', 'cost': 3100, 'prog': 64, 'status': 'ongoing', 'start': '2020-10-01', 'end': '2025-08-31', 'revised': None, 'exp': 1984},
            {'id': 'PROJ-026', 'name': 'Durgapur Steel City Power Plant Modernization', 'ministry': 'Ministry of Power', 'state': 'West Bengal', 'district': 'Paschim Bardhaman', 'agency': 'DVC', 'cost': 5200, 'prog': 45, 'status': 'delayed', 'start': '2020-01-10', 'end': '2024-06-30', 'revised': 5800, 'exp': 2340},
            {'id': 'PROJ-027', 'name': 'Kalyani AIIMS Campus Development', 'ministry': 'Ministry of Health', 'state': 'West Bengal', 'district': 'Nadia', 'agency': 'CPWD', 'cost': 1750, 'prog': 100, 'status': 'completed', 'start': '2019-04-01', 'end': '2023-12-15', 'revised': None, 'exp': 1750},
            {'id': 'PROJ-028', 'name': 'New Town Salt Lake Solar Smart Lighting Grid', 'ministry': 'Ministry of Power', 'state': 'West Bengal', 'district': 'North 24 Parganas', 'agency': 'WBHIDCO', 'cost': 420, 'prog': 100, 'status': 'completed', 'start': '2021-05-15', 'end': '2024-02-28', 'revised': None, 'exp': 420},
            {'id': 'PROJ-029', 'name': 'Murshidabad Bhagirathi River Flood Management', 'ministry': 'Ministry of Water Resources', 'state': 'West Bengal', 'district': 'Murshidabad', 'agency': 'Irrigation & Waterways Dept', 'cost': 1400, 'prog': 35, 'status': 'ongoing', 'start': '2022-01-10', 'end': '2026-03-31', 'revised': None, 'exp': 490},
            {'id': 'PROJ-030', 'name': 'Cooch Behar Regional Airport Upgrade', 'ministry': 'Ministry of Civil Aviation', 'state': 'West Bengal', 'district': 'Cooch Behar', 'agency': 'AAI', 'cost': 380, 'prog': 92, 'status': 'ongoing', 'start': '2021-02-01', 'end': '2025-01-31', 'revised': None, 'exp': 349},
            {'id': 'PROJ-031', 'name': 'Barasat-Bongaon Highway Expansion (NH-112)', 'ministry': 'Ministry of Road Transport', 'state': 'West Bengal', 'district': 'North 24 Parganas', 'agency': 'NHAI', 'cost': 2150, 'prog': 22, 'status': 'delayed', 'start': '2020-07-01', 'end': '2024-09-30', 'revised': 2400, 'exp': 473},
            {'id': 'PROJ-032', 'name': 'Howrah Drainage Basin Sewerage Overhaul', 'ministry': 'Ministry of Urban Development', 'state': 'West Bengal', 'district': 'Howrah', 'agency': 'HMC', 'cost': 1650, 'prog': 50, 'status': 'ongoing', 'start': '2021-08-15', 'end': '2025-12-31', 'revised': None, 'exp': 825},
            {'id': 'PROJ-033', 'name': 'Bankura Rural Drinking Water Supply Scheme', 'ministry': 'Ministry of Water Resources', 'state': 'West Bengal', 'district': 'Bankura', 'agency': 'WBPHED', 'cost': 1280, 'prog': 80, 'status': 'ongoing', 'start': '2020-11-01', 'end': '2025-04-30', 'revised': None, 'exp': 1024},
            {'id': 'PROJ-034', 'name': 'Farakka Lock Gate Modernization', 'ministry': 'Ministry of Shipping', 'state': 'West Bengal', 'district': 'Murshidabad', 'agency': 'IWAI', 'cost': 950, 'prog': 78, 'status': 'ongoing', 'start': '2020-03-01', 'end': '2025-05-31', 'revised': None, 'exp': 741},
            {'id': 'PROJ-035', 'name': 'Bengal Clean Energy Wind-Solar Farm', 'ministry': 'Ministry of Power', 'state': 'West Bengal', 'district': 'Bankura', 'agency': 'WBSEDCL', 'cost': 3300, 'prog': 15, 'status': 'ongoing', 'start': '2023-01-15', 'end': '2027-03-31', 'revised': None, 'exp': 495},
            {'id': 'PROJ-036', 'name': 'Burdwan Railway Station Passenger Terminal', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'Purba Bardhaman', 'agency': 'Eastern Railway', 'cost': 620, 'prog': 100, 'status': 'completed', 'start': '2019-10-01', 'end': '2023-09-30', 'revised': None, 'exp': 620},
            {'id': 'PROJ-037', 'name': 'Guwahati Multimodal Logistics Park', 'ministry': 'Ministry of Shipping', 'state': 'Assam', 'district': 'Kamrup Metropolitan', 'agency': 'SDCL', 'cost': 1100, 'prog': 60, 'status': 'ongoing', 'start': '2021-06-01', 'end': '2025-10-31', 'revised': None, 'exp': 660},
            {'id': 'PROJ-038', 'name': 'Kolkata Riverfront Heritage & Promenade', 'ministry': 'Ministry of Urban Development', 'state': 'West Bengal', 'district': 'Kolkata', 'agency': 'KMDA', 'cost': 890, 'prog': 42, 'status': 'ongoing', 'start': '2022-05-01', 'end': '2026-02-28', 'revised': None, 'exp': 373},
            {'id': 'PROJ-039', 'name': 'Jalpaiguri Circuit Bench Building', 'ministry': 'Ministry of Housing', 'state': 'West Bengal', 'district': 'Jalpaiguri', 'agency': 'PWD West Bengal', 'cost': 480, 'prog': 95, 'status': 'ongoing', 'start': '2020-02-15', 'end': '2025-01-31', 'revised': None, 'exp': 456},
            {'id': 'PROJ-040', 'name': 'North Bengal Medical College Trauma Centre', 'ministry': 'Ministry of Health', 'state': 'West Bengal', 'district': 'Darjeeling', 'agency': 'PWD West Bengal', 'cost': 520, 'prog': 68, 'status': 'ongoing', 'start': '2021-01-10', 'end': '2025-07-31', 'revised': None, 'exp': 353},
            {'id': 'PROJ-041', 'name': 'Bagdogra Airport New Integrated Terminal', 'ministry': 'Ministry of Civil Aviation', 'state': 'West Bengal', 'district': 'Darjeeling', 'agency': 'AAI', 'cost': 1880, 'prog': 20, 'status': 'ongoing', 'start': '2023-03-01', 'end': '2027-06-30', 'revised': None, 'exp': 376},
            {'id': 'PROJ-042', 'name': 'Bhubaneswar IT Park Expansion', 'ministry': 'Ministry of Electronics & IT', 'state': 'Odisha', 'district': 'Khordha', 'agency': 'IDCO', 'cost': 740, 'prog': 35, 'status': 'ongoing', 'start': '2022-04-15', 'end': '2026-01-31', 'revised': None, 'exp': 259},
            {'id': 'PROJ-043', 'name': 'Hooghly Cable Stayed Bridge Preservation', 'ministry': 'Ministry of Road Transport', 'state': 'West Bengal', 'district': 'Hooghly', 'agency': 'HRBC', 'cost': 310, 'prog': 85, 'status': 'ongoing', 'start': '2021-09-01', 'end': '2024-11-30', 'revised': None, 'exp': 263},
            {'id': 'PROJ-044', 'name': 'Purulia Eco-Tourism & Highway Corridor', 'ministry': 'Ministry of Road Transport', 'state': 'West Bengal', 'district': 'Purulia', 'agency': 'PWD West Bengal', 'cost': 920, 'prog': 55, 'status': 'ongoing', 'start': '2021-12-01', 'end': '2025-09-30', 'revised': None, 'exp': 506},
            {'id': 'PROJ-045', 'name': 'Bolpur Shantiniketan Cultural Infrastructure Node', 'ministry': 'Ministry of Urban Development', 'state': 'West Bengal', 'district': 'Birbhum', 'agency': 'SSDA', 'cost': 410, 'prog': 90, 'status': 'ongoing', 'start': '2020-11-15', 'end': '2024-12-31', 'revised': None, 'exp': 369},
            {'id': 'PROJ-046', 'name': 'Birbhum Coal Corridor Rail Link', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'Birbhum', 'agency': 'Eastern Railway', 'cost': 2900, 'prog': 12, 'status': 'delayed', 'start': '2021-08-01', 'end': '2024-08-31', 'revised': 3200, 'exp': 348},
            {'id': 'PROJ-047', 'name': 'Medinipur Super Specialty Cancer Care Block', 'ministry': 'Ministry of Health', 'state': 'West Bengal', 'district': 'Paschim Medinipur', 'agency': 'WBMED', 'cost': 780, 'prog': 48, 'status': 'ongoing', 'start': '2022-02-10', 'end': '2025-11-30', 'revised': None, 'exp': 374},
            {'id': 'PROJ-048', 'name': 'Jhargram Tribal Belt Rural Electrification Grid', 'ministry': 'Ministry of Power', 'state': 'West Bengal', 'district': 'Jhargram', 'agency': 'WBSEDCL', 'cost': 860, 'prog': 72, 'status': 'ongoing', 'start': '2020-08-01', 'end': '2025-03-31', 'revised': None, 'exp': 619},
            {'id': 'PROJ-049', 'name': 'Patna Metro Rail Project', 'ministry': 'Ministry of Railways', 'state': 'Bihar', 'district': 'Patna', 'agency': 'PMRC', 'cost': 13350, 'prog': 25, 'status': 'ongoing', 'start': '2020-05-01', 'end': '2025-10-31', 'revised': None, 'exp': 3337},
            {'id': 'PROJ-050', 'name': 'Tarakeswar Transit Node & Pilgrim Terminal', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'Hooghly', 'agency': 'Eastern Railway', 'cost': 450, 'prog': 82, 'status': 'ongoing', 'start': '2021-03-15', 'end': '2025-01-31', 'revised': None, 'exp': 369},
            {'id': 'PROJ-051', 'name': 'Dankuni Freight Logistics Park Hub', 'ministry': 'Ministry of Railways', 'state': 'West Bengal', 'district': 'Hooghly', 'agency': 'DFCCIL', 'cost': 2400, 'prog': 5, 'status': 'not_started', 'start': '2024-05-01', 'end': '2027-12-31', 'revised': None, 'exp': 120},
            {'id': 'PROJ-052', 'name': 'Kochi Water Metro Expansion', 'ministry': 'Ministry of Urban Development', 'state': 'Kerala', 'district': 'Ernakulam', 'agency': 'KMRL', 'cost': 980, 'prog': 88, 'status': 'ongoing', 'start': '2021-01-01', 'end': '2024-12-31', 'revised': None, 'exp': 862},
            {'id': 'PROJ-053', 'name': 'Midnapore Solar Microgrid Network', 'ministry': 'Ministry of Power', 'state': 'West Bengal', 'district': 'Paschim Medinipur', 'agency': 'WBREDA', 'cost': 620, 'prog': 0, 'status': 'not_started', 'start': '2024-09-01', 'end': '2026-08-31', 'revised': None, 'exp': 0},
            {'id': 'PROJ-054', 'name': 'Ludhiana Smart Industrial Park', 'ministry': 'Ministry of Urban Development', 'state': 'Punjab', 'district': 'Ludhiana', 'agency': 'PSIEC', 'cost': 1150, 'prog': 8, 'status': 'not_started', 'start': '2024-04-15', 'end': '2027-03-31', 'revised': None, 'exp': 92},
        ]

        self.stdout.write(self.style.WARNING('Creating 54 infrastructure projects across states...'))

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
                    'approved_cost': Decimal(p_data['cost']),
                    'revised_cost': Decimal(p_data['revised']) if p_data['revised'] else None,
                    'expenditure': Decimal(p_data['exp']),
                    'start_date': date.fromisoformat(p_data['start']),
                    'expected_completion': date.fromisoformat(p_data['end']),
                    'physical_progress': Decimal(p_data['prog']),
                    'financial_progress': Decimal(financial_progress),
                    'status': p_data['status'],
                    'description': f"Infrastructure project: {p_data['name']} in {p_data['state']}."
                }
            )

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

        self.stdout.write(self.style.SUCCESS('Successfully seeded 54 projects across states.'))
