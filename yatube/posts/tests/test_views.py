import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_another_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_another_client.force_login(self.another_user)

    def test_pages_show_correct_context(self):
        """
        Шаблоны index, group_list, profile
        сформированы с правильным контекстом.
        """
        pages_reverse_name = [
            INDEX_URL,
            GROUP_LIST_URL,
            PROFILE_URL,
            self.POST_DETAIL_URL
        ]
        for reverse_name in pages_reverse_name:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                if reverse_name == self.POST_DETAIL_URL:
                    post = response.context.get('post')
                else:
                    post = response.context['page_obj'][0]
                    self.assertEqual(len(response.context['page_obj']), 1)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.image, self.post.image)

    def test_no_post_on_page(self):
        """
        В выбранную группу не попадает пост,
        относящийся к другой группе.
        """
        self.assertNotIn(
            self.post,
            self.authorized_client.get(
                NEW_GROUP_LIST_URL
            ).context['page_obj']
        )

    def test_author_on_sheet(self):
        """
        Запись попала в профиль автора,
        которым была создана
        """
        self.assertEqual(
            self.user,
            self.authorized_client.get(
                PROFILE_URL
            ).context.get('author')
        )

    def test_group_in_group_list(self):
        """
        Запись попала в группу,
        для которой была создана
        """
        group_items = self.authorized_client.get(
            GROUP_LIST_URL
        ).context['group']
        self.assertEqual(self.group.id, group_items.id)
        self.assertEqual(self.group.title, group_items.title)
        self.assertEqual(self.group.slug, group_items.slug)
        self.assertEqual(self.group.description, group_items.description)

    def test_follow(self):
        all_follows = set(Follow.objects.all())
        self.authorized_client.get(FOLLOW_URL)
        follows = set(Follow.objects.all()) - all_follows
        self.assertEqual(len(follows), 1)
        follow = follows.pop()
        self.assertEqual(follow.author, self.another_user)
        self.assertEqual(follow.user, self.user)

    def test_unfollow(self):
        self.authorized_client.get(FOLLOW_URL)
        all_follows = set(Follow.objects.all())
        self.authorized_client.get(UNFOLLOW_URL)
        follows = all_follows - set(Follow.objects.all())
        self.assertEqual(len(follows), 1)

    def test_post_is_add_to_followers(self):
        self.authorized_client.get(FOLLOW_URL)
        all_posts = set(
            self.authorized_client.get(FOLLOW_INDEX_URL).context['page_obj']
        )
        new_post = Post.objects.create(
            author=self.another_user,
            text='Тест',
            group=self.group,
        )
        posts = set(
            self.authorized_client.get(FOLLOW_INDEX_URL).context['page_obj']
        ) - all_posts
        self.assertEqual(len(posts), 1)
        post = posts.pop()
        self.assertEqual(post.author, new_post.author)
        self.assertEqual(post.text, new_post.text)
        self.assertEqual(post.group, new_post.group)
        self.assertEqual(post.id, new_post.id)

    def test_post_is_not_add_to_another_users(self):
        all_posts = set(
            self.authorized_client.get(FOLLOW_INDEX_URL).context['page_obj']
        )
        Post.objects.create(
            author=self.another_user,
            text='Тест',
            group=self.group,
        )
        posts = set(
            self.authorized_client.get(FOLLOW_INDEX_URL).context['page_obj']
        ) - all_posts
        self.assertEqual(len(posts), 0)


class PaginatorViewsTest(TestCase):
    def test_pages_contains_right_quantity_records(self):
        """
        Паджинация для шаблонов index, group_list, profile
        работает корректно.
        """
        self.user = User.objects.create_user(username=USERNAME)
        self.another_user = User.objects.create_user(username=ANOTHER_USERMANE)
        self.authorized_client = Client()
        self.authorized_another_client = Client()
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug=TEST_SLUG,
            description='Тестовое описание',
        )
        self.authorized_client.force_login(self.user)
        self.authorized_another_client.force_login(self.another_user)
        self.authorized_client.get(FOLLOW_URL)
        Post.objects.bulk_create(
            (
                Post(
                    author=self.user,
                    text=str(text),
                    group=self.group
                ) for text in range(
                    settings.POSTS_COUNT_ON_PAGE + COUNT_POSTS_ON_SECOND_PAGE
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
