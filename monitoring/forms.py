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
