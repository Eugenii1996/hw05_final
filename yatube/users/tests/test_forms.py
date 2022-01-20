from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class CreateUserTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_create_user(self):
        """Валидная форма создает запись в User."""
        no_user = User.objects.count()
        form_data = {
            'username': 'ivan',
            'password1': '1233224568Gdfgdfg',
            'password2': '1233224568Gdfgdfg'
        }
        self.guest_client.post(
            reverse('users:signup'),
            data=form_data
        )
        self.assertNotEqual(User.objects.count(), no_user)
