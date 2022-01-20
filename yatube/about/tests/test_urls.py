from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_author(self):
        """Страница /author/ доступна по заданному адресу."""
        response = self.guest_client.get(reverse('about:author'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_tech(self):
        """Страница /tech/ доступна по заданному адресу."""
        response = self.guest_client.get(reverse('about:tech'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
