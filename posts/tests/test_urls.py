import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Group, Post, Comment


User = get_user_model()
SLUG = 'test_slug'
INDEX_URL = '/'
FOLLOW_URL = '/follow/'
NEW_URL = '/new/'
GROUP_URL = f'/group/{SLUG}/'
URL_404 = '/wrong_address/'
IMG = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
       b'\x01\x00\x80\x00\x00\x00\x00\x00'
       b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
       b'\x00\x00\x00\x2C\x00\x00\x00\x00'
       b'\x02\x00\x01\x00\x00\x02\x02\x0C'
       b'\x0A\x00\x3B')


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=IMG,
            content_type='image/gif',
        )
        cls.user_john = User.objects.create(username='john')
        cls.user_bob = User.objects.create(username='bob')
        cls.group = Group.objects.create(
            title='Test title',
            description='About group',
            slug=SLUG,
        )
        posts_list = []
        for i in range(1, 15):
            posts_list.append(Post(
                text='Test multiple text ' + str(i),
                author=cls.user_bob,
            ))
        Post.objects.bulk_create(posts_list)
        cls.post = Post.objects.create(
            author=cls.user_bob,
            text='Тестовый пост Боба.',
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_john,
            text='Тестовый комментарий Джона к посту Боба.',
        )
        cls.profile_url = f'/{cls.post.author.username}/'
        cls.post_url = f'/{cls.post.author.username}/{cls.post.id}/'
        cls.post_edit_url = f'/{cls.post.author.username}/{cls.post.id}/edit/'
        cls.comment_url = f'/{cls.post.author.username}/{cls.post.id}/comment/'
        cls.user_follow_url = f'/{cls.post.author.username}/follow/'
        cls.user_unfollow_url = f'/{cls.post.author.username}/unfollow/'

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.client_bob = Client()
        self.client_john = Client()
        self.client_bob.force_login(PostsURLTests.user_bob)
        self.client_john.force_login(PostsURLTests.user_john)

    def test_urls_uses_correct_template(self):
        """URL-address uses corresponding template."""
        templates_url_names = {
            INDEX_URL: 'index.html',
            NEW_URL: 'posts/new.html',
            GROUP_URL: 'group.html',
            FOLLOW_URL: 'follow.html',
            URL_404: 'misc/404.html',
            self.profile_url: 'profile.html',
            self.post_url: 'post.html',
            self.post_edit_url: 'posts/new.html',
        }
        for url_name, template in templates_url_names.items():
            with self.subTest(url_name=url_name):
                response = self.client_bob.get(url_name)
                self.assertTemplateUsed(response, template)

    def test_unauthorized_user_permited_urls(self):
        """Certain URL-addresses are permited for unauthorized user."""
        templates_url_names = {
            INDEX_URL: 200,
            NEW_URL: 302,
            GROUP_URL: 200,
            FOLLOW_URL: 302,
            URL_404: 404,
            self.profile_url: 200,
            self.post_url: 200,
            self.post_edit_url: 302,
        }
        for url_name, value in templates_url_names.items():
            with self.subTest(url_name=url_name):
                response = self.guest_client.get(url_name)
                self.assertEqual(response.status_code, value,)

    def test_authorized_user_and_post_author_permited_urls(self):
        """Certain URL-addresses are permited for authorized user
        who is post author.
        """
        templates_url_names = {
            INDEX_URL: 200,
            NEW_URL: 200,
            GROUP_URL: 200,
            FOLLOW_URL: 200,
            URL_404: 404,
            self.profile_url: 200,
            self.post_url: 200,
            self.post_edit_url: 200,
        }
        for url_name, value in templates_url_names.items():
            with self.subTest(url_name=url_name):
                response = self.client_bob.get(url_name)
                self.assertEqual(response.status_code, value)

    def test_post_edit_url_not_permitted_for_authorized_user_not_author(self):
        """URL-address for post edit is not permitted for authorized user
        but not post author.
        """
        response = self.client_john.get(self.post_edit_url)
        self.assertEqual(response.status_code, 302)

    def test_post_edit_url_redirect_anonymous_user(self):
        response = self.guest_client.get(self.post_edit_url, follow=True)
        self.assertRedirects(response, self.post_url)

    def test_post_edit_url_redirect_authorized_user_not_author(self):
        response = self.client_john.get(self.post_edit_url, follow=True)
        self.assertRedirects(response, self.post_url)

    def test_pointed_urls_redirect_anonymous_user_to_login(self):
        post = PostsURLTests.post
        author = post.author.username
        templates_urls = {
            NEW_URL: '/auth/login/?next=/new/',
            FOLLOW_URL: '/auth/login/?next=/follow/',
            self.comment_url: f'/auth/login/?next=/{author}/{post.id}/comment/',
            self.user_follow_url: f'/auth/login/?next=/{author}/follow/',
            self.user_unfollow_url: f'/auth/login/?next=/{author}/unfollow/',
        }
        for url_name, redirect_address in templates_urls.items():
            with self.subTest(url_name=url_name):
                response = self.guest_client.get(url_name)
                self.assertRedirects(response, redirect_address)

    def test_pointed_urls_redirects_authorized_user_as_desired(self):
        templates_urls = {
            self.user_follow_url: self.profile_url,
            self.user_unfollow_url: self.profile_url,
            self.comment_url: self.post_url,
        }
        for url_name, redirect_url in templates_urls.items():
            with self.subTest(url_name=url_name):
                response = self.client_bob.get(url_name)
                self.assertRedirects(response, redirect_url)

    def test_index_cache(self):
        response_first = self.guest_client.get(INDEX_URL)
        Post.objects.create(
            text="Cache testing post",
            author=PostsURLTests.user_bob,
        )
        response_second = self.guest_client.get(INDEX_URL)
        self.assertEqual(response_first.content, response_second.content)
        cache.clear()
        response_third = self.guest_client.get(INDEX_URL)
        self.assertNotEqual(response_first.content, response_third.content)
