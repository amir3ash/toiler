from django.contrib.auth import password_validation, get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.core.files.images import get_image_dimensions
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer, Serializer, CharField
from storages.backends.s3boto3 import S3Boto3Storage

from user.models import User

storage = S3Boto3Storage()


class UserSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'avatar']
        read_only_fields = ['id', 'username', 'avatar']


class UserSearchSerializer(UserSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar']
        read_only_fields = fields


class AvatarSerializer(UserSerializer):
    MAX_AVATAR_SIZE = 1024 * 1024 * 3

    def validate_avatar(self, avatar: InMemoryUploadedFile):
        if avatar is None:
            return None
        try:
            # validate content type
            main, sub = avatar.content_type.split('/')
            if not (main == 'image' and sub in ['jpeg', 'png']):
                raise ValidationError(u'Please use a JPEG or PNG image.')

            w, h = get_image_dimensions(avatar)

            # validate dimensions
            max_width = max_height = 9000
            if w > max_width or h > max_height:
                raise ValidationError(
                    u'Please use an image that is '
                    '%s x %s pixels or smaller.' % (max_width, max_height))

            # validate file size
            if len(avatar) > self.MAX_AVATAR_SIZE:
                raise ValidationError(
                    'Avatar file size may not exceed 3MB.')

        except AttributeError:
            """
            Handles case when we are updating the user profile
            and do not supply a new avatar
            """
            pass

        return avatar

    def update(self, instance: User, validated_data):
        # avatar: InMemoryUploadedFile = validated_data.get('avatar')
        instance_avatar_name = instance.avatar.name if instance.avatar else None

        if instance_avatar_name and storage.exists(instance_avatar_name):
            storage.delete(instance_avatar_name)

        return super(AvatarSerializer, self).update(instance, validated_data)

    class Meta:
        model = get_user_model()
        fields = ['avatar']
        # read_only_fields = fields


class PasswordSerializer(Serializer):
    old_password = CharField(required=True)
    new_password1 = CharField(required=True)
    new_password2 = CharField(required=True)

    def __init__(self, user=None, **kwargs):
        self.user = user
        super().__init__(**kwargs)

    def validate_old_password(self, value):
        """
        Validate that the old_password field is correct.
        """
        old_password = value
        if not self.user.check_password(old_password):
            raise ValidationError(
                PasswordChangeForm.error_messages["password_incorrect"],
                code="password_incorrect",
            )
        return old_password

    def validate_new_password2(self, value):
        password1 = self.initial_data.get("new_password1")
        password2 = value
        if password1 and password2:
            if password1 != password2:
                raise ValidationError(
                    PasswordChangeForm.error_messages["password_mismatch"],
                    code="password_mismatch",
                )
        user = self.user
        password_validation.validate_password(password2, user)
        return password2

    def save(self, commit=True):
        password = self.validated_data["new_password1"]
        user = self.user
        user.set_password(password)
        if commit:
            user.save()
            return user

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
