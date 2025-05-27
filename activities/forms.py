from django.forms import ModelForm, DateInput, Select, SelectMultiple, RadioSelect

from cases.models import task, hearing


class TaskForm(ModelForm):
    class Meta:
        model = task
        widgets = {
            'due_date': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'assign_date': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'assignee': Select(attrs={'class': 'form-select select2'}),
            'shared_with': SelectMultiple(attrs={'class': 'form-select select2'}),
            'task_status': Select(attrs={'class': 'form-check', 'disabled': True}),
        }
        fields = ('title', 'description', 'task_category', 'assignee','task_status','assign_date','due_date')

    def __init__(self, *args, **kwargs):
        mode = kwargs.pop("mode",'create')
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['assign_date'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['due_date'].input_formats = ('%Y-%m-%dT%H:%M',)
        restricted_fields = [
            "comments",
        ]

        if mode not in ["edit", "view"]:
            for field in restricted_fields:
                self.fields.pop(field, None)  # Remove these fields in "create" mode



class HearingForm(ModelForm):
    class Meta:
        model = hearing
        widgets = {
            'hearing_date': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'assignee': Select(attrs={'class': 'form-select select2'}),
            'court': Select(attrs={'class': 'form-select select2'}),
            'priority': Select(attrs={'class': 'form-select select2'}),
            'hearing_status': Select(attrs={'class': 'form-check', 'disabled': True}),
        }

        fields = ('name', 'hearing_date', 'assignee','court','comments_by_lawyer','priority','hearing_status')

    def __init__(self, *args, **kwargs):
        mode = kwargs.pop("mode",'create')
        super(HearingForm, self).__init__(*args, **kwargs)

        restricted_fields = [
            "comments",
        ]
        if mode not in ["edit", "view"]:
            for field in restricted_fields:
                self.fields.pop(field, None)  # Remove these fields in "create" mode

from django import forms

class ContactForm1(forms.Form):
    subject = forms.CharField(max_length=100)
    sender = forms.EmailField()
    leave_message = forms.BooleanField(required=False)

class ContactForm2(forms.Form):
    message = forms.CharField(widget=forms.Textarea)