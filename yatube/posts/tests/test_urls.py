from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from ..models import Group, Post, User


USERNAME = 'auth'
SLUG = 'test-slug'

INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
GROUP_LIST_URL = reverse('posts:group_list', args=[SLUG])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
LOGIN_URL = reverse('users:login')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
FOLLOW_URL = reverse('posts:profile_follow', args=[USERNAME])
UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USERNAME])
REDIRECT_POST_CREATE_URL = f'{LOGIN_URL}?next={POST_CREATE_URL}'
REDIRECT_INDEX_FOLLOW_URL = f'{LOGIN_URL}?next={FOLLOW_INDEX_URL}'
REDIRECT_FOLLOW_URL = f'{LOGIN_URL}?next={FOLLOW_URL}'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.another_user = User.objects.create_user(username='creator')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест',
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            args=[cls.post.id]
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            args=[cls.post.id]
        )
        cls.COMMENT_CREATE_URL = reverse(
            'posts:add_comment',
            args=[cls.post.id]
        )
        cls.REDIRECT_POST_EDIT_URL = (
            f'{LOGIN_URL}?next={cls.POST_EDIT_URL}'
        )
        cls.REDIRECT_COMMENT_CREATE_URL = (
            f'{LOGIN_URL}?next={cls.COMMENT_CREATE_URL}'
        )

    def setUp(self):
        self.guest = Client()
        self.author = Client()
        self.another = Client()
        self.author.force_login(self.user)
        self.another.force_login(self.another_user)

    # Проверяем общедоступные страницы
    def test_urls_uses_correct(self):
        """Любому пользователю доступны URL-адреса."""
        tested_cases = [
            [INDEX_URL, self.guest, HTTPStatus.OK],
            [GROUP_LIST_URL, self.guest, HTTPStatus.OK],
            [PROFILE_URL, self.guest, HTTPStatus.OK],
            [self.POST_DETAIL_URL, self.guest, HTTPStatus.OK],
            ['/unexisting_page/', self.guest, HTTPStatus.NOT_FOUND],
            [self.POST_EDIT_URL, self.author, HTTPStatus.OK],
            [self.POST_EDIT_URL, self.guest, HTTPStatus.FOUND],
            [self.POST_EDIT_URL, self.another, HTTPStatus.FOUND],
            [POST_CREATE_URL, self.another, HTTPStatus.OK],
            [POST_CREATE_URL, self.guest, HTTPStatus.FOUND],
            [self.COMMENT_CREATE_URL, self.guest, HTTPStatus.FOUND],
            [FOLLOW_INDEX_URL, self.another, HTTPStatus.OK],
            [FOLLOW_INDEX_URL, self.guest, HTTPStatus.FOUND],
            [FOLLOW_URL, self.guest, HTTPStatus.FOUND],
            [FOLLOW_URL, self.another, HTTPStatus.FOUND],
            [UNFOLLOW_URL, self.guest, HTTPStatus.FOUND]
        ]
        for address, client, status in tested_cases:
            with self.subTest(address=address, client=client):
                self.assertEqual(
                    client.get(address).status_code, status)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = [
            [INDEX_URL, 'posts/index.html'],
            [GROUP_LIST_URL, 'posts/group_list.html'],
            [PROFILE_URL, 'posts/profile.html'],
            [self.POST_DETAIL_URL, 'posts/post_detail.html'],
            [self.POST_EDIT_URL, 'posts/create_post.html'],
            [POST_CREATE_URL, 'posts/create_post.html'],
            [FOLLOW_INDEX_URL, 'posts/follow.html']
        ]
        for url, template in templates_url_names:
            with self.subTest(url=url):
                self.assertTemplateUsed(self.author.get(url), template)

    def test_redirects(self):
        """
        Неавторизированный пользователь
        перенаправляется на страницу входа.
        """
        redirect_url_names = [
            [POST_CREATE_URL, self.guest, REDIRECT_POST_CREATE_URL],
            [self.POST_EDIT_URL, self.guest, self.REDIRECT_POST_EDIT_URL],
            [self.POST_EDIT_URL, self.another, self.POST_DETAIL_URL],
            [
                self.COMMENT_CREATE_URL,
                self.guest,
                self.REDIRECT_COMMENT_CREATE_URL
            ],
            [FOLLOW_INDEX_URL, self.guest, REDIRECT_INDEX_FOLLOW_URL],
            [FOLLOW_URL, self.guest, REDIRECT_FOLLOW_URL],
            [FOLLOW_URL, self.another, PROFILE_URL],
            [UNFOLLOW_URL, self.another, PROFILE_URL]
        ]
        for url, client, redirect_url in redirect_url_names:
            with self.subTest(url=url, client=client):
                self.assertRedirects(client.get(url), redirect_url)
