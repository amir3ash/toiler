from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.files.images import get_image_dimensions

from .models import TempUser, User


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
            w, h = get_image_dimensions(avatar)

            # validate dimensions
            max_width = max_height = 1000
            if w > max_width or h > max_height:
                print(1)
                raise forms.ValidationError(
                    u'Please use an image that is '
                    '%s x %s pixels or smaller.' % (max_width, max_height))

            # validate content type
            main, sub = avatar.content_type.split('/')
            if not (main == 'image' and sub in ['jpeg', 'png']):
                print(2)
                raise forms.ValidationError(u'Please use a JPEG or PNG image.')

            # validate file size
            if len(avatar) > (20 * 1024):
                print(3)
                raise forms.ValidationError(
                    u'Avatar file size may not exceed 20k.')

        except AttributeError:
            """
            Handles case when we are updating the user profile
            and do not supply a new avatar
            """
            pass

        return avatar

    def save(self, commit=True, user=None):
        if user is None:
            return

        user.avatar = self.cleaned_data['avatar']
        if commit:
            user.save(update_fields=['avatar'])


class AccountSettings(forms.Form):
    first_name = forms.CharField(required=False, max_length=30)
    last_name = forms.CharField(required=False, max_length=30)
    email = forms.EmailField(required=False)


class DeleteAccount(forms.Form):
    delete_account = forms.BooleanField(required=True)
