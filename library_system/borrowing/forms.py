from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import BorrowRecord
from accounts.models import CustomUser


class BorrowForm(forms.ModelForm):
    class Meta:
        model = BorrowRecord
        fields = ['member', 'book', 'due_date', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['member'].queryset = CustomUser.objects.filter(
            role='student', is_active=True
        )
        self.fields['due_date'].initial = (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        for name, field in self.fields.items():
            if field.widget.__class__.__name__ not in ('CheckboxInput',):
                field.widget.attrs['class'] = 'form-control'

    def clean_due_date(self):
        due = self.cleaned_data.get('due_date')
        if due and due <= timezone.now().date():
            raise forms.ValidationError('Due date must be in the future.')
        return due

    def clean(self):
        cleaned = super().clean()
        book = cleaned.get('book')
        if book and not book.is_available:
            self.add_error('book', 'This book is not available for borrowing.')
        return cleaned


class ReturnForm(forms.ModelForm):
    class Meta:
        model = BorrowRecord
        fields = ['returned_date', 'fine_paid', 'notes']
        widgets = {
            'returned_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['returned_date'].initial = timezone.now().strftime('%Y-%m-%d')
        for name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'CheckboxInput':
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean_returned_date(self):
        date = self.cleaned_data.get('returned_date')
        if date and date > timezone.now().date():
            raise forms.ValidationError('Return date cannot be in the future.')
        return date
