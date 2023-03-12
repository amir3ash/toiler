from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .img_util import optimize_image, validate_image, ImageValidationError
from .models import User


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(required=True, max_length=150, help_text='Required.')
    last_name = forms.CharField(required=False, max_length=150, help_text='Required.')
    email = forms.EmailField(required=True)

    class Meta:
        model = User  # TODO CHANGE IT TO TEMPUSER
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)

    def save(self, commit=True, email=True):
        user: User = super(RegisterForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_active = True
        if commit:
            user.save()
            # if email:
            #     user.email_user()  # if error occurred it will delete TempUser

        return user


class AvatarForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('avatar',)

    def clean_avatar(self):
        avatar = self.cleaned_data['avatar']

        try:
            validate_image(avatar)

        except ImageValidationError as e:
            raise forms.ValidationError(e)

        return avatar

    def save(self, commit=True, user=None):
        if user is None:
            return

        avatar = self.cleaned_data['avatar']
        user.avatar = optimize_image(avatar)

        if commit:
            user.save(update_fields=['avatar'])


class AccountSettings(forms.Form):
    first_name = forms.CharField(required=False, max_length=30)
    last_name = forms.CharField(required=False, max_length=30)
    email = forms.EmailField(required=False)


class DeleteAccount(forms.Form):
    delete_account = forms.BooleanField(required=True)
