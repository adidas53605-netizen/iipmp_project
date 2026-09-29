from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from monitoring.validators import ComplexPasswordValidator
from monitoring.models import UserProfile, FailedLoginAttempt

class SecurityTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.validator = ComplexPasswordValidator()
        self.user = User.objects.create_user(username='officer1', email='officer1@iipmp.gov.in', password='Password@123')
        self.profile = UserProfile.objects.create(user=self.user, role='field_officer')

        self.admin = User.objects.create_superuser(username='admin1', password='AdminPassword@123', email='admin@iipmp.gov.in')
        self.admin_profile = UserProfile.objects.create(user=self.admin, role='admin')

    def test_password_validator_valid(self):
        try:
            self.validator.validate('SecureP@ss123')
        except ValidationError:
            self.fail("ComplexPasswordValidator raised ValidationError unexpectedly for valid password!")

    def test_password_validator_invalid(self):
        invalid_passwords = [
            'short1!',          # < 8 chars
            'lowercase123!',    # no uppercase
            'UPPERCASE123!',    # no lowercase
            'NoNumbersHere!',   # no digits
            'NoSpecialChars12',  # no special chars
        ]
        for pwd in invalid_passwords:
            with self.subTest(pwd=pwd):
                with self.assertRaises(ValidationError):
                    self.validator.validate(pwd)

    def test_account_lockout_after_five_attempts(self):
        login_url = reverse('login')
        email = 'lockout_test@iipmp.gov.in'
        # Request OTP first
        self.client.post(login_url, {'email': email, 'step': 'request_otp'})
        
        for i in range(1, 5):
            response = self.client.post(login_url, {'step': 'verify_otp', 'email': email, 'otp_code': '000000'})
            self.assertContains(response, "Invalid OTP")
        
        # 5th failed attempt should trigger lockout
        response = self.client.post(login_url, {'step': 'verify_otp', 'email': email, 'otp_code': '000000'})
        self.assertContains(response, "Account locked")

    def test_otp_verification_flow(self):
        login_url = reverse('login')
        email = 'otp_test@iipmp.gov.in'
        # 1. Request OTP -> Should render OTP step context with show_otp=True
        response = self.client.post(login_url, {'email': email, 'step': 'request_otp'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['show_otp'])
        otp_data = cache.get(f"otp_data_{email}")
        self.assertIsNotNone(otp_data)
        otp_code = otp_data['code']
        self.assertEqual(len(otp_code), 6)

        # 2. Invalid OTP -> Should display error message
        resp_wrong = self.client.post(login_url, {'step': 'verify_otp', 'email': email, 'otp_code': '000000'})
        self.assertEqual(resp_wrong.status_code, 200)
        self.assertContains(resp_wrong, "Invalid OTP")

        # 3. Correct OTP -> Should log in and redirect to dashboard
        resp_correct = self.client.post(login_url, {'step': 'verify_otp', 'email': email, 'otp_code': otp_code})
        self.assertRedirects(resp_correct, reverse('dashboard'))

    def test_expired_otp_rejection(self):
        login_url = reverse('login')
        email = 'expired_test@iipmp.gov.in'
        # Request OTP
        self.client.post(login_url, {'email': email, 'step': 'request_otp'})
        otp_data = cache.get(f"otp_data_{email}")
        self.assertIsNotNone(otp_data)
        otp_code = otp_data['code']
        # Set expiry to past timestamp in cache and session
        otp_data['expires_at'] = 0
        cache.set(f"otp_data_{email}", otp_data, timeout=300)

        session = self.client.session
        session['pending_otp_expires'] = 0
        session.save()

        # Attempt verification -> Backend should reject with 'OTP expired'
        response = self.client.post(login_url, {'step': 'verify_otp', 'email': email, 'otp_code': otp_code})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "OTP expired")

    def test_rbac_access_control(self):
        # Field officer trying to access project create page should be denied (403)
        self.client.login(username='officer1', password='Password@123')
        response = self.client.get(reverse('project_add'))
        self.assertEqual(response.status_code, 403)

        # Admin user should access project create page successfully
        self.client.login(username='admin1', password='AdminPassword@123')
        response = self.client.get(reverse('project_add'))
        self.assertEqual(response.status_code, 200)

    def test_admin_login_portal(self):
        admin_login_url = reverse('admin_login')
        response = self.client.get(admin_login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Authentication")

    def test_project_status_counts_sum_to_total(self):
        from monitoring.models import Project
        from datetime import date
        Project.objects.all().delete()
        Project.objects.create(project_id='P1', name='Proj 1', ministry='M1', state='WB', approved_cost=10, start_date=date.today(), expected_completion=date.today(), status='ongoing', risk_level='high')
        Project.objects.create(project_id='P2', name='Proj 2', ministry='M1', state='WB', approved_cost=10, start_date=date.today(), expected_completion=date.today(), status='completed', risk_level='low')
        Project.objects.create(project_id='P3', name='Proj 3', ministry='M1', state='WB', approved_cost=10, start_date=date.today(), expected_completion=date.today(), status='delayed', risk_level='high')
        Project.objects.create(project_id='P4', name='Proj 4', ministry='M1', state='WB', approved_cost=10, start_date=date.today(), expected_completion=date.today(), status='not_started', risk_level='medium')

        self.client.login(username='admin1', password='AdminPassword@123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        total = response.context['total_projects']
        ongoing = response.context['ongoing_count']
        completed = response.context['completed_count']
        delayed = response.context['delayed_count']
        on_hold = response.context['not_started_count']

        self.assertEqual(total, 4)
        self.assertEqual(ongoing + completed + delayed + on_hold, total)

