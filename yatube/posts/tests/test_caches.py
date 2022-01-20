from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


INDEX_URL = reverse('posts:index')


class CacheTests(TestCase):
    def test_caches(self):
        """Выполняется кэширование главной страницы."""
        user = User.objects.create_user(username='auth')
        Post.objects.create(author=user, text='Тест')
        first_responce = Client().get(INDEX_URL)
        Post.objects.all().delete()
        second_responce = Client().get(INDEX_URL)
        self.assertEqual(
            first_responce.content,
            second_responce.content
        )
        cache.clear()
        third_responce = Client().get(INDEX_URL)
        self.assertNotEqual(
            second_responce.content,
            third_responce.content
        )
