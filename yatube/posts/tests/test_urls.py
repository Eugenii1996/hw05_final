from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from ..models import Group, Post, User


USERNAME = 'auth'
ANOTHER_USERMANE = 'creator'
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
REDIRECT_UNFOLLOW_URL = f'{LOGIN_URL}?next={UNFOLLOW_URL}'

OK_STATUS = HTTPStatus.OK
FOUND_STATUS = HTTPStatus.FOUND
NOT_FOUND_STATUS = HTTPStatus.NOT_FOUND


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.another_user = User.objects.create_user(username=ANOTHER_USERMANE)
        cls.guest = Client()
        cls.author = Client()
        cls.another = Client()
        cls.author.force_login(cls.user)
        cls.another.force_login(cls.another_user)
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

    # Проверяем общедоступные страницы
    def test_urls_uses_correct(self):
        """Любому пользователю доступны URL-адреса."""
        tested_cases = [
            [INDEX_URL, self.guest, OK_STATUS],
            [GROUP_LIST_URL, self.guest, OK_STATUS],
            [PROFILE_URL, self.guest, OK_STATUS],
            [self.POST_DETAIL_URL, self.guest, OK_STATUS],
            ['/unexisting_page/', self.guest, NOT_FOUND_STATUS],
            [self.POST_EDIT_URL, self.author, OK_STATUS],
            [self.POST_EDIT_URL, self.guest, FOUND_STATUS],
            [self.POST_EDIT_URL, self.another, FOUND_STATUS],
            [POST_CREATE_URL, self.another, OK_STATUS],
            [POST_CREATE_URL, self.guest, FOUND_STATUS],
            [self.COMMENT_CREATE_URL, self.guest, FOUND_STATUS],
            [FOLLOW_INDEX_URL, self.another, OK_STATUS],
            [FOLLOW_INDEX_URL, self.guest, FOUND_STATUS],
            [FOLLOW_URL, self.guest, FOUND_STATUS],
            [FOLLOW_URL, self.author, FOUND_STATUS],
            [FOLLOW_URL, self.another, FOUND_STATUS],
            [UNFOLLOW_URL, self.guest, FOUND_STATUS],
            [UNFOLLOW_URL, self.author, NOT_FOUND_STATUS],
            [UNFOLLOW_URL, self.another, FOUND_STATUS]
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
            [FOLLOW_URL, self.author, PROFILE_URL],
            [UNFOLLOW_URL, self.guest, REDIRECT_UNFOLLOW_URL],
            [UNFOLLOW_URL, self.another, PROFILE_URL]
        ]
        for url, client, redirect_url in redirect_url_names:
            with self.subTest(url=url, client=client):
                self.assertRedirects(client.get(url), redirect_url)
