from django import forms
from core.models import documents,Path

class DocumentForm(forms.ModelForm):
    class Meta:
        model = documents
        fields = ['name', 'attachment']
