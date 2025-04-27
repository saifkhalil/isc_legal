from django.forms import ModelForm, DateInput, Select, SelectMultiple, RadioSelect
from django_select2 import forms as s2forms

from cases.models import LitigationCases


class UserWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "username__icontains",
        "email__icontains",
    ]
    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("data-theme", "bootstrap-5")  # Set Select2 Bootstrap 5 theme
        return attrs

class CourtWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "name__icontains",
    ]
    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("data-theme", "bootstrap-5")  # Set Select2 Bootstrap 5 theme
        return attrs

class SharedWithWidget(s2forms.ModelSelect2MultipleWidget):
    search_fields = [
        "username__icontains",
        "email__icontains",
    ]
    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.setdefault("data-theme", "bootstrap-5")  # Set Select2 Bootstrap 5 theme
        return attrs

class CaseForm(ModelForm):
    class Meta:
        model = LitigationCases

        widgets = {
            'start_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'assignee':Select(attrs={'class': 'form-select select2'}),
            'shared_with':SelectMultiple(attrs={'class': 'form-select select2'}),
            'court':Select(attrs={'class': 'form-select select2'}),
            'case_category':RadioSelect(attrs={'class': 'form-check'}),
            'characteristic':RadioSelect(attrs={'class': 'form-check'}),
            'case_status': Select(attrs={'class': 'form-check','disabled': True}),
        }
        fields = ('case_type','Stage','court','name','description','case_category','characteristic', 'case_status','judge','detective', 'internal_ref_number','priority','start_time','end_time','assignee','shared_with','client_position','opponent_position','case_close_status','case_close_comment','ImportantDevelopment','comments')

    def __init__(self, *args, **kwargs):
        mode = kwargs.pop("mode")
        super(CaseForm, self).__init__(*args, **kwargs)
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