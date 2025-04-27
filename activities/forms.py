from django.forms import ModelForm

from cases.models import task, hearing


class TaskForm(ModelForm):
    class Meta:
        model = task
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)


class HearingForm(ModelForm):
    class Meta:
        model = hearing
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(HearingForm, self).__init__(*args, **kwargs)