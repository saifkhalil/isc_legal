from django import forms
from django.contrib.auth import authenticate
# from phonenumber_field.formfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _

# from phonenumber_field.widgets import PhoneNumberInternationalFallbackWidget, PhoneNumberPrefixWidget
from accounts.models import User


# class RegistrationForm(UserCreationForm):
#     email = forms.EmailField(
#         max_length=254, help_text=_('Required. Add a valid email address.'))
#     phone = PhoneNumberField(widget=PhoneNumberPrefixWidget(initial='IQ'))
#     phone.error_messages['invalid'] = _(
#         'Enter a valid phone number (e.g. 7801000000).')
#     i_agree = forms.BooleanField(label=_("Policy for terms of use"), error_messages={'required': _('You must accept to policy for terms of use')}, widget=forms.widgets.CheckboxInput(
#         attrs={'class': 'form-check-input'}))

#     class Meta:
#         model = User
#         fields = ('email', 'username', 'firstname', 'lastname',
#                   'phone', 'password1', 'password2', 'i_agree', )
#         # error_messages = {
#         #     'phone' : {
#         #         'required' : "Enter a valid phone number (e.g. 7801000000)."
#         #     }
#         # }


class UserAuthenticationForm(forms.ModelForm):

    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput,help_text=_('Enter your password'))
    email = forms.EmailField(label=_('Email'), widget=forms.PasswordInput,help_text=_('Enter your email'))

    class Meta:
        model = User
        fields = ('email', 'password')

    def clean(self):
        if self.is_valid():
            email = self.cleaned_data['email']
            password = self.cleaned_data['password']
            if not authenticate(email=email, password=password):
                raise forms.ValidationError(_("Invalid login"))


# class UserUpdateForm(forms.ModelForm):

#     class Meta:
#         model = User
#         fields = ('email', 'username', 'firstname', 'lastname', 'phone')

#     def clean_email(self):
#         email = self.cleaned_data['email']
#         try:
#             User = User.objects.exclude(pk=self.instance.pk).get(email=email)
#         except User.DoesNotExist:
#             return email
#         raise forms.ValidationError('Email "%s" is already in use.' % User)

#     def clean_username(self):
#         username = self.cleaned_data['username']
#         try:
#             User = User.objects.exclude(
#                 pk=self.instance.pk).get(username=username)
#         except User.DoesNotExist:
#             return username
#         raise forms.ValidationError(
#             'Username "%s" is already in use.' % username)

# class SetPasswordForm(forms.Form):
#     new_password1 = forms.CharField(
#         label=_("New password"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
#         help_text=password_validation.password_validators_help_text_html(),
#     )
#     new_password2 = forms.CharField(
#         label=_("New password confirmation"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
#     )
#
#     def clean(self):
#         cleaned_data = super().clean()
#         new_password1 = cleaned_data.get("new_password1")
#         new_password2 = cleaned_data.get("new_password2")
#         if new_password1 and new_password2 and new_password1 != new_password2:
#             raise forms.ValidationError(_("The two password fields didn't match."))
#
#         password_validation.validate_password(new_password2)
#         return cleaned_data

