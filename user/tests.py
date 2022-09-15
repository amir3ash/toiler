import logging

from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth import views as auth_views

import user.views
from django.test import TestCase, SimpleTestCase

# Create your tests here.
from user.forms import RegisterForm
from user.models import TempUser


class IndexTestCase(SimpleTestCase):
    # for not using database

    def test_index_page(self):
        self.assertTrue(0 == 0, 'this is zero')


class TestStatus(TestCase):
    # for database

    def test_login_exist(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200, 'login page status code')
        self.assertEqual(response.resolver_match.func.__name__, auth_views.LoginView.as_view().__name__, 'hello istgse')
        self.assertTemplateUsed(response, 'login.html')

    def test_create_userd(self):
        test_password = '647654DFA$%$%fkfkhh'
        test_username = 'test'

        # self.client.post('/user/create',
        #                  data={'first_name': 'amir',
        #                        'last_name': 'shams',
        #                        'email': 'amir@hello.cpm',
        #                        'password1': 'heisheisgood',
        #                        'password2': 'heisheisgood'},
        #                  )
        form = RegisterForm(data={'first_name': 'amir',
                                  'last_name': 'shams',
                                  'username': test_username,
                                  'email': 'amir@hello.cpm',
                                  'password1': test_password,
                                  'password2': test_password
                                  },
                            )
        print('error', form.errors, form.error_messages)
        self.assertTrue(form.is_valid())
        form.save(email=False)

        response = self.client.post(reverse('login'), {'username': test_username, 'password': '464878978'},
                                    CONTENT_TYPE='application/json',ACCEPT='application/json')

        print(response.status_code,response.headers, response.content)

        # token_generator = default_token_generator
        # token = token_generator.make_token(self)
        # uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # response = self.client.get(f'/activate/{uidb64}/{token}')

    def test_slash(self):
        response = self.client.get('/', {'foo': 'bar', 'age': 58}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200, "this is first page.")
