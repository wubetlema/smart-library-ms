from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

INPUT_CLASS = {'class': 'form-control'}
TEXTAREA_CLASS = {'class': 'form-control', 'rows': 2}


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs=INPUT_CLASS))
    first_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs=INPUT_CLASS))
    last_name = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs=INPUT_CLASS))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs=INPUT_CLASS))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs=TEXTAREA_CLASS))
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email',
                  'phone', 'address', 'date_of_birth', 'password1', 'password2']
        widgets = {'username': forms.TextInput(attrs=INPUT_CLASS)}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(attrs=INPUT_CLASS)
        self.fields['password2'].widget = forms.PasswordInput(attrs=INPUT_CLASS)
        self.fields['username'].widget.attrs.update(INPUT_CLASS)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={**INPUT_CLASS, 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={**INPUT_CLASS, 'placeholder': 'Password'}))


class ProfileUpdateForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'address',
                  'date_of_birth', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'profile_picture' and 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'


class AdminUserEditForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email',
                  'phone', 'address', 'date_of_birth', 'role', 'is_approved', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if field.widget.__class__.__name__ == 'CheckboxInput':
                field.widget.attrs['class'] = 'form-check-input'
            elif 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
