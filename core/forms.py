from django import forms
from core.models import documents,Path
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import os


class DocumentForm(forms.ModelForm):
    class Meta:
        model = documents
        fields = ['name', 'attachment']

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')

        allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx','.ppt','.pptx'
                              '.jpg', '.jpeg', '.png', '.gif', '.bmp','.tif', '.tiff']

        if attachment:
            ext = os.path.splitext(attachment.name)[1].lower()  # Get file extension
            if ext not in allowed_extensions:
                raise ValidationError(
                    _('Unsupported file type: %(ext)s. Allowed types are: %(types)s.'),
                    code='invalid_extension',
                    params={'ext': ext, 'types': allowed_extensions}
                )

        return attachment