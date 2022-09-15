import datetime
from functools import wraps

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from rest_framework import status, generics
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from user.forms import RegisterForm, AvatarForm
from user.models import TempUser
from user.serializers import UserSerializer, PasswordSerializer, UserSearchSerializer, AvatarSerializer


def index(request):
    return render(request, 'index.html')


@login_required(login_url='login')
def change_avatar(request):
    if request.method == 'POST':
        form = AvatarForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(user=request.user)
            return JsonResponse({'msg': 'Ok'}, status=status.HTTP_200_OK)

        else:
            return JsonResponse({'msg': 'Bad request.'}, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse({'msg': 'Method not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class Avatar(generics.CreateAPIView):
    serializer_class = AvatarSerializer

    def get_object(self):
        return self.request.user

    def post(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class SettingApiView(RetrieveUpdateAPIView, GenericAPIView):
    """
    View to get and change user info.
    """
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class SearchUsersByUsername(ListAPIView, GenericAPIView):
    serializer_class = UserSearchSerializer
    queryset = get_user_model().objects.all()
    filter_backends = [SearchFilter]
    search_fields = ('username',)  # TODO write tests
    ordering_fields = []


class ChangePassword(APIView):
    """
    View to change password by providing old one.
    """

    def get_serializer(self, *args, **kwargs):
        return PasswordSerializer(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = request.user
        serializer = self.get_serializer(user=instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({'msg': 'password changed'})

    def perform_update(self, serializer):
        serializer.save()

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


def cast_temp_to_user(user: TempUser):
    newuser: User = User(first_name=user.first_name,
                         last_name=user.last_name,
                         username=user.username,
                         date_joined=user.date_joined,
                         email=user.email)

    newuser.password = user.password
    return newuser


_activate_email_url = 'activate-account'
INTERNAL_ACTIVATE_SESSION_TOKEN = 'email_confirmation_token'


def validate_email(request, uidb64, token):
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['allow'] = ','.join(['GET'])
        return response

    if request.method == 'GET':
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            print('uid:', uid)
            user = TempUser.objects.get(pk=uid)
            print('user:', user)
        except(TypeError, ValueError, OverflowError, TempUser.DoesNotExist):
            user = None
            return render(request, 'validation_done.html', {'error': True}, status=status.HTTP_406_NOT_ACCEPTABLE)

        if token == _activate_email_url:
            session_token = request.session.get(INTERNAL_ACTIVATE_SESSION_TOKEN)

            if user is not None and default_token_generator.check_token(user, session_token):
                new_user: User = cast_temp_to_user(user)
                new_user.is_active = True
                # print(new_user, new_user.password, new_user.password == user.password, new_user.email == user.email,
                #       new_user.email)

                new_user.save()

                TempUser.objects.filter(username=user.username).delete()  # delete all TempUser with this username

                return render(request, 'validation_done.html', status=201)

            else:
                return render(request, 'validation_done.html', {'error': True}, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            if default_token_generator.check_token(user, token):
                # Store the token in the session and redirect to the
                # password reset form at a URL without the token. That
                # avoids the possibility of leaking the token in the
                # HTTP Referer header.
                request.session[INTERNAL_ACTIVATE_SESSION_TOKEN] = token
                redirect_url = request.path.replace(token, _activate_email_url)
                return HttpResponseRedirect(redirect_url)

    else:
        return JsonResponse({}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


def validating_email_sent(request):
    return render(request, 'valid_email_sent.html')


def check_recaptcha(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        request.valid_recaptcha = None
        if request.method == 'POST':
            recaptcha_response = request.POST.get('g-recaptcha-response')
            data = {
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': recaptcha_response,
                'remoteip': get_client_ip(request)
            }
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            result = r.json()
            if result['success']:
                request.recaptcha_is_valid = True
                # print('recaptcha is passed.')
            else:
                request.recaptcha_is_valid = False
                return HttpResponseForbidden()

        return view_func(request, *args, **kwargs)

    return _wrapped_view


@check_recaptcha
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if request.recaptcha_is_valid and form.is_valid():
            same_user = TempUser.objects.filter(username=form.cleaned_data.get('username'),
                                                email=form.cleaned_data.get('email'))[:1]
            if same_user:
                same_user = same_user[0]
                if (same_user.date_joined + datetime.timedelta(0, settings.PASSWORD_RESET_TIMEOUT)) \
                        > datetime.datetime.now():
                    same_user.delete()
                    print(f'User {same_user.username} has been registered and token expired.')
                else:
                    print(f'User {same_user.username} tries to register twice.')
                    return render(request, 'register.html', {'errors': 'Email has been sent. Please check your inbox.'})

            user = form.save()

            # u = authenticate(username=form.cleaned_data.get('username'), password=form.clean_password2())
            # if u is not None:
            #     print('ok it works')
            #     # Sequence.objects.create(user=user)

        else:
            print(form.error_messages)
            errors = form.errors.as_data().get('password2')
            context = {
                'errors': errors,
                'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY
            }
            return render(request, 'register.html', context, status=status.HTTP_406_NOT_ACCEPTABLE)

        # if username and password and len(username) > 2 and len(password) > 3:
        #     user = User.objects.create_user(username, email=email, password=password)
        #
        #     request_time = time.process_time() - start
        #     logger.info("Request completed in {}ms".format(request_time))
        #
        #     return JsonResponse({"msg": "user created", "token": "nothing", "userID": user.pk},
        #                         status=status.HTTP_201_CREATED)
        # return JsonResponse({"msg": "username or password must be longer"}, status=status.HTTP_406_NOT_ACCEPTABLE)
        return redirect(reverse('valid_email_sent'))
    if request.method == 'GET':
        context = {
            'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY
        }
        return render(request, 'register.html', context=context)


# not work. vulnerable to IP Spoofing
def get_client_ip(request):
    arvan_ip = request.META.get('HTTP_AR_REAL_IP')
    x_original_forwarded_for = request.META.get('HTTP_X_ORIGINAL_FORWARDED_FOR')
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if arvan_ip:
        ip = arvan_ip.split(', ')[-1]
    elif x_original_forwarded_for:
        ip = x_original_forwarded_for.split(', ')[-1]
    elif x_forwarded_for:
        ip = x_forwarded_for.split(', ')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
# I tried this, and it works:
#
# UPDATE SQLITE_SEQUENCE SET seq = <n> WHERE name = '<table>'
#
# Where n+1 is the next ROWID you want and table is the table name.
