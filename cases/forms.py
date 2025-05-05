from django.forms import ModelForm, DateInput, Select, SelectMultiple, RadioSelect,Textarea
from django_select2 import forms as s2forms

from cases.models import LitigationCases, Notation, AdministrativeInvestigation


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

class NotationForm(ModelForm):
    class Meta:
        model = Notation

        widgets = {
            'description': Textarea(attrs={'rows': '3'}, ),
            'start_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'reference_date': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'notation_date': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'assignee':Select(attrs={'class': 'form-select select2'}),
            'shared_with':SelectMultiple(attrs={'class': 'form-select select2'}),
            'court':Select(attrs={'class': 'form-select select2'}),
            'case_status': Select(attrs={'class': 'form-check','disabled': True}),
            'priority': Select(attrs={'class': 'form-check'}),
        }
        fields = ('subject','description','start_time','end_time','reference_date','notation_date','requester', 'court','judge','detective','priority','assignee','shared_with',)

    def __init__(self, *args, **kwargs):
        mode = kwargs.pop("mode")
        super(NotationForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['end_time'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['reference_date'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['notation_date'].input_formats = ('%Y-%m-%dT%H:%M',)
        restricted_fields = [
            "ImportantDevelopment",
            "comments",
        ]

        if mode not in ["edit", "view"]:
            for field in restricted_fields:
                self.fields.pop(field, None)  # Remove these fields in "create" mode

class AdministrativeInvestigationForm(ModelForm):
    class Meta:
        model = AdministrativeInvestigation

        widgets = {
            'start_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': DateInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'assignee':Select(attrs={'class': 'form-select select2'}),
            'shared_with':SelectMultiple(attrs={'class': 'form-select select2'}),
            'priority': Select(attrs={'class': 'form-check'}),
            'members':SelectMultiple(attrs={'class': 'form-select select2'}),
            'chairman': Select(attrs={'class': 'form-select select2'}),
        }
        fields = ('subject','admin_order_number','chairman','members','priority','start_time','end_time','assignee','shared_with',)

    def __init__(self, *args, **kwargs):
        mode = kwargs.pop("mode")
        super(AdministrativeInvestigationForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].input_formats = ('%Y-%m-%dT%H:%M',)
        self.fields['end_time'].input_formats = ('%Y-%m-%dT%H:%M',)
        restricted_fields = [
            "ImportantDevelopment",
            "comments",
        ]

        if mode not in ["edit", "view"]:
            for field in restricted_fields:
                self.fields.pop(field, None)  # Remove these fields in "create" mode

