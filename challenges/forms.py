from django import forms
from .models import *

class ChallengeSubmitForm(forms.ModelForm):
    class Meta:
        model = ChallengeSubmission
        fields = ['code']
        widgets = {
            'code': forms.Textarea(attrs={'class': 'font-mono', 'rows': 20}),
        }
        labels = {'code': 'Ваше решение'}

class ChallengeGenerationForm(forms.Form):
    language = forms.ChoiceField(choices=Challenge.LANGUAGE_CHOICES)
    difficulty = forms.ChoiceField(choices=Challenge.DIFFICULTY_CHOICES)