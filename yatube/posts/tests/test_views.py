import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from ..models import Follow, Group, Post, User


USERNAME = 'auth'
ANOTHER_USERMANE = 'creator'
TEST_SLUG = 'test-slug'
NEW_TEST_SLUG = 'newtest-slug'

INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
GROUP_LIST_URL = reverse('posts:group_list', args=[TEST_SLUG])
NEW_GROUP_LIST_URL = reverse('posts:group_list', args=[NEW_TEST_SLUG])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
FOLLOW_INDEX_URL = reverse('posts:follow_index')
FOLLOW_URL = reverse('posts:profile_follow', args=[ANOTHER_USERMANE])
UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[ANOTHER_USERMANE])

COUNT_POSTS_ON_SECOND_PAGE = 2

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.another_user = User.objects.create_user(username=ANOTHER_USERMANE)
        cls.authorized_client = Client()
        cls.authorized_another_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_another_client.force_login(cls.another_user)
        Follow.objects.create(
            user=cls.user,
            author=cls.another_user
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=TEST_SLUG,
            description='Тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug=NEW_TEST_SLUG,
            description='Тестовое описание',
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест',
            group=cls.group,
            image=cls.uploaded
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            args=[cls.post.id]
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_show_correct_context(self):
        """
        Шаблоны index, group_list, profile
        сформированы с правильным контекстом.
        """
        Follow.objects.create(
            user=self.another_user,
            author=self.user
        )
        pages_reverse_name = [
            INDEX_URL,
            GROUP_LIST_URL,
            PROFILE_URL,
            self.POST_DETAIL_URL,
            FOLLOW_INDEX_URL
        ]
        for url in pages_reverse_name:
            with self.subTest(url=url):
                if url == FOLLOW_INDEX_URL:
                    response = self.authorized_another_client.get(url)
                else:
                    response = self.authorized_client.get(url)
                if url == self.POST_DETAIL_URL:
                    post = response.context.get('post')
                else:
                    posts = set(response.context['page_obj'])
                    self.assertEqual(len(posts), 1)
                    post = posts.pop()
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.image, self.post.image)

    def test_no_post_on_page(self):
        """
        В выбранную группу не попадает пост,
        относящийся к другой группе,
        На страницу подписок пользователя не попадает
        пост автора, на которого пользователь не подписан.
        """
        pages_reverse_name = [
            NEW_GROUP_LIST_URL,
            FOLLOW_INDEX_URL
        ]
        self.assertNotIn(
            self.post,
            self.authorized_another_client.get(
                NEW_GROUP_LIST_URL
            ).context['page_obj']
        )
        for url in pages_reverse_name:
            with self.subTest(url=url):
                self.assertNotIn(
                    self.post,
                    self.authorized_client.get(url).context['page_obj']
                )

    def test_author_on_sheet(self):
        """
        Имя авторизованного клиента совпадает
        с именем профиля пользователя
        """
        self.assertEqual(
            self.user,
            self.authorized_client.get(
                PROFILE_URL
            ).context.get('author')
        )

    def test_group_in_group_list(self):
        """Группа создалась с правильным содержанием полей"""
        group_items = self.authorized_client.get(
            GROUP_LIST_URL
        ).context['group']
        self.assertEqual(self.group.id, group_items.id)
        self.assertEqual(self.group.title, group_items.title)
        self.assertEqual(self.group.slug, group_items.slug)
        self.assertEqual(self.group.description, group_items.description)

    def test_follow(self):
        self.authorized_client.get(FOLLOW_URL)
        self.assertEqual(
            Follow.objects.get(user=self.user).author, self.another_user
        )

    def test_unfollow(self):
        self.authorized_client.get(UNFOLLOW_URL)
        self.assertNotIn(self.user, Follow.objects.all())

    def test_caches(self):
        """Выполняется кэширование главной страницы."""
        Post.objects.create(author=self.user, text='Тест')
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

    def test_pages_contains_right_quantity_records(self):
        """
        Паджинация для шаблонов index, group_list, profile
        работает корректно.
        """
        Post.objects.bulk_create(
            (
                Post(
                    author=self.user,
                    text=str(text),
                    group=self.group
                ) for text in range(
                    settings.POSTS_COUNT_ON_PAGE
                    + COUNT_POSTS_ON_SECOND_PAGE
                    - 1
                )
            )
        )
        page_objects = {
            INDEX_URL: settings.POSTS_COUNT_ON_PAGE,
            f'{INDEX_URL}?page=2': COUNT_POSTS_ON_SECOND_PAGE,
            GROUP_LIST_URL: settings.POSTS_COUNT_ON_PAGE,
            f'{GROUP_LIST_URL}?page=2': COUNT_POSTS_ON_SECOND_PAGE,
            PROFILE_URL: settings.POSTS_COUNT_ON_PAGE,
            f'{PROFILE_URL}?page=2': COUNT_POSTS_ON_SECOND_PAGE,
        }
        for url, records_count in page_objects.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), records_count
                )
