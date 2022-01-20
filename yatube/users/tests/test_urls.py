from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

User = get_user_model()


class UsersURLTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """
        Страницы доступны любому
        пользователю по заданным адресам.
        """
        url_names = [
            reverse('users:signup'),
            reverse('users:login'),
            reverse('users:password_reset'),
            reverse('users:password_reset_done'),
            reverse('users:password_reset_complete'),
            reverse('users:logout')
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template_authorized(self):
        """
        Страницы доступны авторизованному
        пользователю по заданным адресам.
        """
        url_names = [
            reverse('users:password_change'),
            reverse('users:password_change_done')
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
