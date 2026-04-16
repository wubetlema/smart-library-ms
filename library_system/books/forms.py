from django import forms
from .models import Book, Category


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'isbn', 'category', 'description',
            'publisher', 'publication_year', 'total_copies',
            'available_copies', 'cover_image', 'cover_url', 'read_url',
            'pdf_file', 'status',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'publication_year': forms.NumberInput(attrs={'min': 1000, 'max': 2100, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'cover_image' and 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get('total_copies')
        available = cleaned.get('available_copies')
        if total is not None and available is not None and available > total:
            self.add_error('available_copies', 'Available copies cannot exceed total copies.')
        return cleaned


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class BookSearchForm(forms.Form):
    q = forms.CharField(
        required=False, label='Search',
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by title, ISBN…',
            'class': 'form-control form-control-sm'
        })
    )
    author = forms.CharField(
        required=False, label='Author',
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by author…',
            'class': 'form-control form-control-sm'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    availability = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('available', 'Available'), ('unavailable', 'Unavailable')],
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
