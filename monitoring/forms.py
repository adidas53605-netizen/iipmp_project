from django import forms
from decimal import Decimal
from .models import Project, Milestone

MINISTRY_CHOICES = [
    ('', 'Select Ministry'),
    ('Ministry of Road Transport', 'Ministry of Road Transport'),
    ('Ministry of Power', 'Ministry of Power'),
    ('Ministry of Urban Development', 'Ministry of Urban Development'),
    ('Ministry of Railways', 'Ministry of Railways'),
    ('Ministry of Water Resources', 'Ministry of Water Resources'),
]

class ProjectForm(forms.ModelForm):
    ministry = forms.ChoiceField(choices=MINISTRY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Project
        exclude = ['created_at', 'updated_at']
        widgets = {
            'project_id': forms.TextInput(attrs={'placeholder': 'Auto-generated if blank (e.g. PROJ-054)'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_completion': forms.DateInput(attrs={'type': 'date'}),
            'physical_progress': forms.NumberInput(attrs={'min': '0', 'max': '100', 'step': '0.1'}),
            'financial_progress': forms.NumberInput(attrs={'min': '0', 'max': '100', 'step': '0.1'}),
            'approved_cost': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'revised_cost': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'expenditure': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'state': forms.TextInput(attrs={'value': 'West Bengal'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project_id'].required = False
        self.fields['start_date'].required = False
        self.fields['financial_progress'].required = False

    def clean(self):
        cleaned_data = super().clean()
        approved_cost = cleaned_data.get('approved_cost')
        revised_cost = cleaned_data.get('revised_cost')
        expenditure = cleaned_data.get('expenditure')
        start_date = cleaned_data.get('start_date')
        expected_completion = cleaned_data.get('expected_completion')
        physical_progress = cleaned_data.get('physical_progress')
        financial_progress = cleaned_data.get('financial_progress')

        if financial_progress is None and approved_cost and expenditure is not None:
            if approved_cost > 0:
                cleaned_data['financial_progress'] = round((Decimal(str(expenditure)) / Decimal(str(approved_cost))) * 100, 2)
            else:
                cleaned_data['financial_progress'] = Decimal('0.00')

        if approved_cost is not None and approved_cost < 0:
            self.add_error('approved_cost', "Approved cost must be >= 0.")
            
        if physical_progress is not None and not (0 <= physical_progress <= 100):
            self.add_error('physical_progress', "Physical progress must be between 0 and 100.")
            
        if financial_progress is not None and not (0 <= financial_progress <= 100):
            self.add_error('financial_progress', "Financial progress must be between 0 and 100.")
            
        if expenditure is not None and expenditure < 0:
            self.add_error('expenditure', "Expenditure must be >= 0.")
            
        if start_date and expected_completion and expected_completion < start_date:
            self.add_error('expected_completion', "Expected completion date cannot be earlier than start date.")
            
        if revised_cost is not None and revised_cost < 0:
            self.add_error('revised_cost', "Revised cost must be >= 0.")
            
        return cleaned_data

class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        exclude = ['project']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date'}),
            'completion_date': forms.DateInput(attrs={'type': 'date'}),
        }

class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label='Select CSV File')

    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            if not csv_file.name.endswith('.csv'):
                raise forms.ValidationError("File must be a CSV.")
        return csv_file

import re
from .models import UserProfile, DASHBOARD_VIEW_CHOICES

STATE_CHOICES = [
    ('', 'Select State/UT'),
    ('West Bengal', 'West Bengal'),
    ('Maharashtra', 'Maharashtra'),
    ('Karnataka', 'Karnataka'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Gujarat', 'Gujarat'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Odisha', 'Odisha'),
    ('Rajasthan', 'Rajasthan'),
    ('Telangana', 'Telangana'),
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Delhi', 'Delhi'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Punjab', 'Punjab'),
    ('Other State/UT', 'Other State/UT'),
]

class UserProfileForm(forms.ModelForm):
    state = forms.ChoiceField(choices=STATE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    ministry = forms.ChoiceField(choices=MINISTRY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = UserProfile
        fields = [
            'full_name', 'phone', 'designation', 'ministry', 'state',
            'employee_id', 'photo', 'email_notifications', 'default_dashboard_view'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Aditya Das'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 9876543210'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Project Director'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. EMP-2026-889'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_dashboard_view': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email_notifications'].required = False
        self.fields['full_name'].required = False
        self.fields['phone'].required = False
        self.fields['designation'].required = False
        self.fields['ministry'].required = False
        self.fields['state'].required = False
        self.fields['employee_id'].required = False
        self.fields['photo'].required = False

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if phone:
            digits = re.sub(r'\D', '', phone)
            if len(digits) == 12 and digits.startswith('91'):
                digits = digits[2:]
            if len(digits) != 10 or not digits.startswith(('6', '7', '8', '9')):
                raise forms.ValidationError("Please enter a valid 10-digit Indian phone number (e.g. 9876543210).")
            return digits
        return ''

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and hasattr(photo, 'size'):
            if photo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Image file size cannot exceed 2 MB.")
            ext = photo.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                raise forms.ValidationError("Unsupported image format. Upload JPG, PNG, WEBP, or GIF.")
        return photo


class ProfileSetupForm(forms.ModelForm):
    state = forms.ChoiceField(choices=STATE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    ministry = forms.ChoiceField(choices=MINISTRY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = UserProfile
        fields = ['full_name', 'designation', 'ministry', 'state', 'phone', 'photo']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Executive Engineer'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional 10-digit phone number'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['full_name'].required = True
        self.fields['designation'].required = True
        self.fields['ministry'].required = True
        self.fields['state'].required = True
        self.fields['phone'].required = False
        self.fields['photo'].required = False

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if phone:
            digits = re.sub(r'\D', '', phone)
            if len(digits) == 12 and digits.startswith('91'):
                digits = digits[2:]
            if len(digits) != 10 or not digits.startswith(('6', '7', '8', '9')):
                raise forms.ValidationError("Please enter a valid 10-digit Indian phone number.")
            return digits
        return ''

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and hasattr(photo, 'size'):
            if photo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Image file size cannot exceed 2 MB.")
            ext = photo.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                raise forms.ValidationError("Unsupported image format. Upload JPG, PNG, WEBP, or GIF.")
        return photo
