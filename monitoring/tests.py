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
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.profile.role = 'field_officer'
        self.profile.profile_completed = True
        self.profile.save()

        self.admin = User.objects.create_superuser(username='admin1', password='AdminPassword@123', email='admin@iipmp.gov.in')
        self.admin_profile, _ = UserProfile.objects.get_or_create(user=self.admin)
        self.admin_profile.role = 'admin'
        self.admin_profile.profile_completed = True
        self.admin_profile.save()

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

        # 3. Correct OTP for new user -> Should log in and redirect to profile_setup (first-time onboarding)
        resp_correct = self.client.post(login_url, {'step': 'verify_otp', 'email': email, 'otp_code': otp_code})
        self.assertRedirects(resp_correct, reverse('profile_setup'))

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

    def test_persistent_login_and_logout(self):
        login_url = reverse('login')
        logout_url = reverse('logout')
        dashboard_url = reverse('dashboard')

        # 1. Unauthenticated request to /dashboard/ should redirect to /login/
        self.client.logout()
        response_unauth = self.client.get(dashboard_url)
        self.assertRedirects(response_unauth, f"{login_url}?next={dashboard_url}")

        # 2. Login via OTP
        email = 'persistent_user@iipmp.gov.in'
        self.client.post(login_url, {'email': email, 'step': 'request_otp'})
        otp_data = cache.get(f"otp_data_{email}")
        self.assertIsNotNone(otp_data)
        otp_code = otp_data['code']

        resp_verify = self.client.post(login_url, {'step': 'verify_otp', 'email': email, 'otp_code': otp_code})
        self.assertRedirects(resp_verify, reverse('profile_setup'))

        user = User.objects.get(email=email)
        user.profile.profile_completed = True
        user.profile.save()

        # Verify session expiry is set to 30 days (2592000 seconds)
        session = self.client.session
        self.assertEqual(session.get_expiry_age(), 30 * 24 * 60 * 60)

        # 3. Authenticated request to /login/ should redirect to /dashboard/
        resp_login_visit = self.client.get(login_url)
        self.assertRedirects(resp_login_visit, dashboard_url)

        # 4. Logout should clear session, delete cookie, and redirect to /login/
        resp_logout = self.client.get(logout_url)
        self.assertRedirects(resp_logout, login_url)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_user_profile_completion_and_views(self):
        self.client.login(username='officer1', password='Password@123')
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "User Profile")

        # Update profile
        update_data = {
            'full_name': 'Aditya Das',
            'phone': '9876543210',
            'designation': 'Senior Director',
            'ministry': 'Ministry of Power',
            'state': 'West Bengal',
            'employee_id': 'EMP-2026-99',
            'default_dashboard_view': 'overview',
            'email_notifications': 'on'
        }
        post_resp = self.client.post(reverse('profile'), update_data)
        self.assertRedirects(post_resp, reverse('profile'))

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, 'Aditya Das')
        self.assertEqual(self.profile.phone, '9876543210')
        self.assertEqual(self.profile.designation, 'Senior Director')
        self.assertGreaterEqual(self.profile.completion_percentage, 80)

    def test_profile_setup_middleware_gate(self):
        # Create user without profile completed
        new_user = User.objects.create_user(username='newbie', email='newbie@iipmp.gov.in', password='Password@123')
        new_profile = UserProfile.objects.get(user=new_user)
        self.assertFalse(new_profile.profile_completed)

        self.client.login(username='newbie', password='Password@123')
        # Accessing dashboard before setup should redirect to /profile/setup/
        resp_gate = self.client.get(reverse('dashboard'))
        self.assertRedirects(resp_gate, reverse('profile_setup'))

        # Submit profile setup form
        setup_data = {
            'full_name': 'Newbie Officer',
            'designation': 'Assistant Nodal Officer',
            'ministry': 'Ministry of Railways',
            'state': 'West Bengal',
            'phone': '9123456789'
        }
        setup_resp = self.client.post(reverse('profile_setup'), setup_data)
        self.assertRedirects(setup_resp, reverse('dashboard'))

        new_profile.refresh_from_db()
        self.assertTrue(new_profile.profile_completed)

        # Accessing dashboard now should succeed
        resp_dashboard = self.client.get(reverse('dashboard'))
        self.assertEqual(resp_dashboard.status_code, 200)



