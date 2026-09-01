from django import forms
from .models import Project, Milestone

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = ['created_at', 'updated_at', 'risk_level']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_completion': forms.DateInput(attrs={'type': 'date'}),
            'physical_progress': forms.NumberInput(attrs={'min': '0', 'max': '100'}),
            'financial_progress': forms.NumberInput(attrs={'min': '0', 'max': '100'}),
            'approved_cost': forms.NumberInput(attrs={'min': '0.01'}),
            'expenditure': forms.NumberInput(attrs={'min': '0'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        approved_cost = cleaned_data.get('approved_cost')
        revised_cost = cleaned_data.get('revised_cost')
        expenditure = cleaned_data.get('expenditure')
        start_date = cleaned_data.get('start_date')
        expected_completion = cleaned_data.get('expected_completion')
        physical_progress = cleaned_data.get('physical_progress')
        financial_progress = cleaned_data.get('financial_progress')

        if approved_cost is not None and approved_cost <= 0:
            self.add_error('approved_cost', "Approved cost must be > 0.")
            
        if physical_progress is not None and not (0 <= physical_progress <= 100):
            self.add_error('physical_progress', "Physical progress must be 0-100.")
            
        if financial_progress is not None and not (0 <= financial_progress <= 100):
            self.add_error('financial_progress', "Financial progress must be 0-100.")
            
        if expenditure is not None and expenditure < 0:
            self.add_error('expenditure', "Expenditure must be >= 0.")
            
        if start_date and expected_completion and expected_completion < start_date:
            self.add_error('expected_completion', "Expected completion must be >= start date.")
            
        if revised_cost is not None and revised_cost <= 0:
            self.add_error('revised_cost', "If revised cost is set, it must be > 0.")
            
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
