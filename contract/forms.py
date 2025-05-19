from django.forms import ModelForm, DateInput, Select, SelectMultiple, RadioSelect,Textarea
from django_select2 import forms as s2forms
from .models import Contract

class ContractForm(ModelForm):
    class Meta:
        model = Contract

        widgets = {
            'start_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'description': Textarea(attrs={'rows': '3'}, ),
            'end_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'assignee':Select(attrs={'class': 'form-select select2'}),
            'shared_with':SelectMultiple(attrs={'class': 'form-select select2'}),
            'court':Select(attrs={'class': 'form-select select2'}),
            'case_category':RadioSelect(attrs={'class': 'form-check'}),
            'characteristic':RadioSelect(attrs={'class': 'form-check'}),
            'case_status': Select(attrs={'class': 'form-check','disabled': True}),
        }
        fields = ('case_type','Stage','court','name','description','case_category','characteristic', 'case_status','judge','detective', 'internal_ref_number','priority','start_time','end_time','assignee','shared_with','client_position','opponent_position','case_close_status','case_close_comment')

    def __init__(self, *args, **kwargs):
        mode = kwargs.pop("mode")
        super(ContractForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['end_time'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields["Stage"].widget.attrs["disabled"] = True
        restricted_fields = [
            "case_close_status",
            "case_close_comment",
            "ImportantDevelopment",
            "comments",
        ]

        if mode not in ["edit", "view"]:
            for field in restricted_fields:
                self.fields.pop(field, None)  # Remove these fields in "create" mode