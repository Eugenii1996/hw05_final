import shutil
import tempfile
from xml.etree.ElementTree import Comment

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms

from ..forms import PostForm
from ..models import Comment, Group, Post, User


USERNAME = 'auth'
ANOTHER_USERMANE = 'creator'

POST_CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
LOGIN_URL = reverse('users:login')

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

MEDIA_DIRECTORY = 'posts/'
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
        cls.notes_group = Group.objects.create(
            title='Заметки',
            slug='notes',
            description='Тестовое описание'
        )
        cls.letters_group = Group.objects.create(
            title='Письма',
            slug='letters',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест',
            group=cls.notes_group
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit',
            args=[cls.post.id]
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            args=[cls.post.id]
        )
        cls.COMMENT_CREATE_URL = reverse(
            'posts:add_comment',
            args=[cls.post.id]
        )
        cls.REDIRECT_POST_EDIT_URL = (
            f'{LOGIN_URL}?next={cls.POST_EDIT_URL}'
        )
        cls.form = PostForm()

    def setUp(self):
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_author_create_post(self):
        """
        Валидная форма создает запись в Post
        для авторизованного пользователя.
        """
        all_posts = set(Post.objects.all())
        form_data = {
            'text': 'Тестовый текст',
            'group': self.notes_group.pk,
            'image': self.uploaded
        }
        response = self.author.post(
            POST_CREATE_URL,
            data=form_data
        )
        posts = set(Post.objects.all()) - all_posts
        self.assertEqual(len(posts), 1)
        post = posts.pop()
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image, f'{MEDIA_DIRECTORY}{form_data["image"]}')

    def test_guest_create_post(self):
        """Валидная форма не создает запись в Post для гостя."""
        all_posts = set(Post.objects.all())
        form_data = {
            'text': 'Тестовый текст',
            'group': self.notes_group.pk,
            'image': self.uploaded
        }
        self.guest.post(
            POST_CREATE_URL,
            data=form_data
        )
        posts = set(Post.objects.all()) - all_posts
        self.assertEqual(len(posts), 0)

    def test_title_label(self):
        """
        Переопределение названий
        полей формы работает корректно.
        """
        form_label_names = {
            'text': 'Текст поста',
            'group': 'Группа'
        }
        for field, name in form_label_names.items():
            self.assertEqual(
                self.form.fields[field].label, name
            )

    def test_title_help_text(self):
        """
        Переопределение комментариев
        полей формы работает корректно.
        """
        form_help_text_names = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, name in form_help_text_names.items():
            self.assertEqual(
                self.form.fields[field].help_text, name
            )

    def test_author_edit_post(self):
        """
        Валидная форма изменяет запись в Post
        для авторизованного автора поста.
        """
        form_data = {
            'text': 'Тестовый текст',
            'group': self.letters_group.pk,
            'image': self.uploaded
        }
        response = self.author.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        post = response.context['post']
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.image, f'{MEDIA_DIRECTORY}{form_data["image"]}')

    def test_another_and_guest_edit_post(self):
        """
        Валидная форма не изменяет запись в Post
        для авторизованного не автора поста
        и для неавторизованного пользователя.
        """
        clients = [
            [self.another, self.POST_DETAIL_URL],
            [self.guest, self.REDIRECT_POST_EDIT_URL]
        ]
        form_data = {
            'text': 'Тестовый текст',
            'group': self.letters_group.pk,
            'image': self.uploaded
        }
        for client, url in clients:
            response = client.post(
                self.POST_EDIT_URL,
                data=form_data,
                follow=True
            )
        post = Post.objects.get(pk=self.post.id)
        self.assertRedirects(response, url)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group.pk, self.post.group.pk)
        self.assertEqual(post.image, self.post.image)

    def test_form_pages_show_correct_context(self):
        """
        Шаблоны post_edit и post_create сформированы
        с правильным контекстом.
        """
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        pages_reverse_name = {
            self.POST_EDIT_URL: form_fields,
            POST_CREATE_URL: form_fields,
        }
        for url, fields_set in pages_reverse_name.items():
            with self.subTest(reverse_name=url):
                response = self.author.get(url)
                for value, expected in fields_set.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form'
                        ).fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_author_create_comment(self):
        """
        Валидная форма создает запись в Comment
        для авторизованного пользователя.
        """
        all_comments = set(Comment.objects.all())
        form_data = {
            'text': 'Тестовый текст'
        }
        response = self.author.post(
            self.COMMENT_CREATE_URL,
            data=form_data
        )
        comments = set(Comment.objects.all()) - all_comments
        self.assertEqual(len(comments), 1)
        comment = comments.pop()
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, self.post)

    def test_guest_create_comment(self):
        """Валидная форма не создает запись в Comment для гостя."""
        all_comments = set(Comment.objects.all())
        form_data = {
            'text': 'Тестовый текст'
        }
        self.guest.post(
            self.COMMENT_CREATE_URL,
            data=form_data
        )
        comments = set(Comment.objects.all()) - all_comments
        self.assertEqual(len(comments), 0)
