from django.test import TestCase
from django.urls import reverse


USER = 'auth'
SLUG = 'test-slug'
POST_ID = 1


class PostURLTests(TestCase):
    def test_routes(self):
        """Маршруты дают ожидаемые upls."""
        route_url_names = [
            ['index', None, '/'],
            ['group_list', [SLUG], f'/group/{SLUG}/'],
            ['profile', [USER], f'/profile/{USER}/'],
            ['post_detail', [POST_ID], f'/posts/{POST_ID}/'],
            ['post_edit', [POST_ID], f'/posts/{POST_ID}/edit/'],
            ['post_create', None, '/create/'],
            ['add_comment', [POST_ID], f'/posts/{POST_ID}/comment/'],
            ['follow_index', None, '/follow/'],
            ['profile_follow', [USER], f'/profile/{USER}/follow/'],
            ['profile_unfollow', [USER], f'/profile/{USER}/unfollow/']
        ]
        for route, arg, url in route_url_names:
            self.assertEqual(
                reverse(f'posts:{route}', args=arg), url
            )
