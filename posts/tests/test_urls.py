import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Group, Post, Comment, Follow


User = get_user_model()
SLUG = 'test_slug'
INDEX_URL = '/'
FOLLOW_URL = '/follow/'
NEW_URL = '/new/'
GROUP_URL = f'/group/{SLUG}/'
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
        cls.follow = Follow.objects.create(
            user=cls.user_john,
            author=cls.user_bob,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_john,
            text='Тестовый комментарий Джона к посту Боба.',
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        post = PostsURLTests.post
        self.guest_client = Client()
        self.client_bob = Client()
        self.client_john = Client()
        self.client_bob.force_login(PostsURLTests.user_bob)
        self.client_john.force_login(PostsURLTests.user_john)
        self.profile_url = f'/{post.author.username}/'
        self.post_url = f'/{post.author.username}/{post.id}/'
        self.post_edit_url = f'/{post.author.username}/{post.id}/edit/'
        self.comment_url = f'/{post.author.username}/{post.id}/comment/'
        self.user_follow_url = f'/{post.author.username}/follow/'
        self.user_unfollow_url = f'/{post.author.username}/unfollow/'

    def test_urls_uses_correct_template(self):
        """URL-address uses corresponding template."""
        templates_url_names = {
            INDEX_URL: 'index.html',
            NEW_URL: 'posts/new.html',
            GROUP_URL: 'group.html',
            FOLLOW_URL: 'follow.html',
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
            self.profile_url: 200,
            self.post_url: 200,
            self.post_edit_url: 302,
            self.comment_url: 302,
            self.user_follow_url: 302,
            self.user_unfollow_url: 302,
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
            self.profile_url: 200,
            self.post_url: 200,
            self.post_edit_url: 200,
            self.comment_url: 302,
            self.user_follow_url: 302,
            self.user_unfollow_url: 302,
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
        """After calling url for post edit by unauthorized user he is
        redirected to post viewing page.
        """
        response = self.guest_client.get(self.post_edit_url, follow=True)
        self.assertRedirects(response, self.post_url)

    def test_post_edit_url_redirect_authorized_user_not_author(self):
        """After calling url for post edit by authorized but not
        post author user he is redirected to post viewing page.
        """
        response = self.client_john.get(self.post_edit_url, follow=True)
        self.assertRedirects(response, self.post_url)

    def test_wrong_url_returns_404_error(self):
        response = self.guest_client.get('/404/')
        self.assertEqual(response.status_code, 404)

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

    def test_user_follow_url_redirect_author(self):
        """If authorized user calls url to follow profile author
        he is redirected to profile viewing page.
        """
        response = self.client_john.get(self.user_follow_url, follow=True)
        self.assertRedirects(response, self.profile_url)

    def test_user_unfollow_url_redirect_authorized_user(self):
        """If authorized user calls url to unfollow profile author
        he is redirected to profile viewing page.
        """
        response = self.client_john.get(self.user_unfollow_url, follow=True)
        self.assertRedirects(response, self.profile_url)

    def test_comment_url_redirect_user(self):
        """If authorized user calls url for post comment he is redirected
        to post viewing page.
        """
        response = self.client_john.get(self.comment_url, follow=True)
        self.assertRedirects(response, self.post_url)
