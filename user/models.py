import requests
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _


class TempUser(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=False,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = models.EmailField(blank=False, max_length=254, verbose_name='email address')
    first_name = models.CharField(blank=False, max_length=150, verbose_name='first name')
    groups = None
    user_permissions = None
    # i don't know is it right?
    is_staff = False
    is_superuser = False

    def email_user(self, subject=None, message=None, from_email=None, **kwargs):
        """Send a Confirmation email to this user.
        If exception occurred, it will delete user """

        # subject = 'Registration Confirmationtest' if not subject else subject

        token_generator = default_token_generator
        token = token_generator.make_token(self)
        uidb64 = urlsafe_base64_encode(force_bytes(self.pk))

        name = self.first_name.title() + (' ' + self.last_name.title() if self.last_name else '')
        link = reverse('validate_email', kwargs={'uidb64': uidb64, 'token': token})
        # context = {
        #     'user': self,
        #     'token': token_generator.make_token(self),
        #     'uidb64': urlsafe_base64_encode(force_bytes(self.pk)),
        #     'domain': 'Toiler.ir',
        # }
        # body = loader.render_to_string('email/registration_confirmation_email.html', context)
        try:
            url = "https://api.sendinblue.com/v3/smtp/email"
            payload = {
                "sender": {
                    "id": 1,
                    # "name": "Toiler",
                    # "email": "noreply@toiler.ir",
                },
                "to": [
                    {
                        "email": self.email,
                        # "name": self.first_name
                    }
                ],
                "params": {
                    "NAME": name,
                    "LINK": f"https://localhost{link}",  # TODO CHANGE IT
                },
                "templateId": 3,
            }
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "api-key": settings.EMAIL_API_PASSWORD
            }

            response = requests.request("POST", url, json=payload, headers=headers)
            if response.status_code == 201:
                print('good!', response.status_code, response.json())
            else:
                print(response.status_code, 'error occurred!', response.json())
            # send_mail(subject, body if not message else message, from_email, [self.email], **kwargs)
        except Exception as e:
            print('Email not sent:', e)
            TempUser.objects.filter(pk=self.pk).delete()
            raise e

    class Meta:
        unique_together = ('username', 'email')


def generate_img_path(instance, filename):
    return filename


class User(AbstractUser):
    avatar = models.ImageField(null=True, blank=True, upload_to=generate_img_path)
