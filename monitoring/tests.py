from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.urls import reverse
from monitoring.validators import ComplexPasswordValidator
from monitoring.models import UserProfile, FailedLoginAttempt

class SecurityTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.validator = ComplexPasswordValidator()
        self.user = User.objects.create_user(username='officer1', password='Password@123')
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
        for i in range(1, 5):
            response = self.client.post(login_url, {'username': 'officer1', 'password': 'WrongPassword123'})
            self.assertContains(response, f"Attempt {i} of 5")
        
        # 5th failed attempt should trigger lockout
        response = self.client.post(login_url, {'username': 'officer1', 'password': 'WrongPassword123'})
        self.assertContains(response, "Account locked")

        attempt = FailedLoginAttempt.objects.get(identifier='officer1')
        self.assertEqual(attempt.failed_count, 5)
        self.assertIsNotNone(attempt.locked_until)

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
