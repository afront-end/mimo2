from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Введите валидный email")

    class Meta:
        model = User
        fields = ['username', 'email'] 
    
    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.help_text = None
            if field_name == 'username':
                field.widget.attrs['placeholder'] = 'Придумайте никнейм'
            elif field_name == 'email':
                field.widget.attrs['placeholder'] = 'example@mail.com'
            elif 'password' in field_name:
                field.widget.attrs['placeholder'] = '••••••••'

class VerificationForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center tracking-widest font-bold text-2xl',
            'placeholder': '000000'
        })
    )