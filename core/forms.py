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
            # Добавляем красивые подсказки внутрь полей
            if field_name == 'username':
                field.widget.attrs['placeholder'] = 'Придумайте никнейм'
            elif field_name == 'email':
                field.widget.attrs['placeholder'] = 'example@mail.com'
            elif 'password' in field_name:
                field.widget.attrs['placeholder'] = '••••••••'