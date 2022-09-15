from django.conf import settings
from django.urls import path
from user import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('register', views.register, name='register'),
    path('login', views.check_recaptcha(auth_views.LoginView.as_view(template_name='login.html',
                                extra_context={'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY})), name='login'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),
    path('account', views.SettingApiView.as_view(), name='account_info'),
    path('change_password', views.ChangePassword.as_view(), name='change_pass'),
    path('upload_avatar', views.change_avatar, name='upload_avatar'),
    path('avatar', views.Avatar.as_view(), name='avatar'),
    path('search_users', views.SearchUsersByUsername.as_view(), name='search_users'),

    path("activate/<uidb64>/<token>/", views.validate_email, name='validate_email'),
    path('activate', views.validating_email_sent, name='valid_email_sent'),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name='reset.html'),
         name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='reset_done.html'),
         name='password_reset_complete'),
    path('reset_password/done', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'),
         name='password_reset_done'),
    path('reset_password', auth_views.PasswordResetView.as_view(
        template_name='reset_password.html',
        email_template_name='email/reset_pass_email.html',
        subject_template_name='reset_pass_email_subject.txt',
        # email_template_name=None,
        extra_email_context={'domain': 'toiler.ir', 'protocol': 'https'}), name='reset_password'),
]
