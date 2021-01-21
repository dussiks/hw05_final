import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post, Follow, Comment


User = get_user_model()
INDEX_URL = reverse('index')
NEW_URL = reverse('new_post')
FOLLOW_URL = reverse('follow_index')
URL_404 = reverse('404')
URL_500 = reverse('500')
IMG = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
       b'\x01\x00\x80\x00\x00\x00\x00\x00'
       b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
       b'\x00\x00\x00\x2C\x00\x00\x00\x00'
       b'\x02\x00\x01\x00\x00\x02\x02\x0C'
       b'\x0A\x00\x3B')
PER_PAGE = settings.PER_PAGE


class PostsViewsTests(TestCase):
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
            title="First test group title",
            description='About first test group',
            slug='slug_one',
        )
        Group.objects.create(
            title="Second test group title",
            description='About second test group',
            slug='slug_two',
        )
        posts_list = []
        for i in range(1, 15):
            posts_list.append(Post(
                text='Test post ' + str(i) + ' number',
                author=cls.user_bob,
            ))
        Post.objects.bulk_create(posts_list)
        Post.objects.create(
            text='Test john first post',
            author=cls.user_john,
            group=Group.objects.get(slug='slug_two'),
        )
        Post.objects.create(
            text='Test john second post',
            author=cls.user_john,
            group=Group.objects.get(slug='slug_two'),
        )
        cls.post = Post.objects.create(
            text='Test bob uniq post',
            author=cls.user_bob,
            group=Group.objects.get(slug='slug_one'),
            image=uploaded,
        )
        cls.follow = Follow.objects.create(
            user=cls.user_john,
            author=cls.user_bob,
        )
        cls.comment = Comment.objects.create(
            author=cls.user_john,
            post=cls.post,
            text='Тестовый комментарий Джона на пост Боба.'
        )
        cls.all_posts = Post.objects.all()
        cls.posts_count = cls.user_bob.posts.count()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.client_bob = Client()
        self.client_john = Client()
        self.client_bob.force_login(PostsViewsTests.user_bob)
        self.client_john.force_login(PostsViewsTests.user_john)

    def test_pages_uses_correct_template(self):
        """Each view-name uses corresponding template."""
        post = PostsViewsTests.post
        author = post.author.username
        templates_page_names = {
            'index.html': INDEX_URL,
            'posts/new.html': NEW_URL,
            'follow.html': FOLLOW_URL,
            'group.html': reverse('group', args=['slug_one']),
            'profile.html': reverse('profile', args=[author]),
            'post.html': reverse('post', args=[author, post.id]),
            'posts/new.html': reverse('post_edit', args=[author, post.id]),
            'misc/404.html': URL_404,
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.client_bob.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_homepage_show_correct_context(self):
        """Template homepage generated with correct context."""
        response = self.client_bob.get(INDEX_URL)
        expected_post = PostsViewsTests.post
        actual_post = response.context.get('page')[0]
        self.assertEqual(actual_post, expected_post)

    def test_follow_page_show_correct_context(self):
        """Template follow page generated with correct context."""
        response = self.client_john.get(FOLLOW_URL)
        expected_post = PostsViewsTests.post
        actual_post = response.context.get('page')[0]
        self.assertEqual(actual_post, expected_post)

    def test_profile_show_correct_context(self):
        """Template profile generated with correct context."""
        author = PostsViewsTests.post.author.username
        response = self.client_bob.get(reverse('profile', args=[author]))
        expected_page_details = {
            PostsViewsTests.post: response.context.get('page')[0],
            PostsViewsTests.posts_count: response.context.get('posts_count'),
            PostsViewsTests.user_bob: response.context.get('author'),
        }
        for key, value in expected_page_details.items():
            with self.subTest(key=key):
                self.assertEqual(key, value)

    def test_group_page_show_correct_context(self):
        """Template group generated with correct context."""
        response = self.client_bob.get(reverse('group', args=['slug_one']))
        expected_page_details = {
            PostsViewsTests.post: response.context.get('page')[0],
            PostsViewsTests.group: response.context.get('group'),
        }
        for key, value in expected_page_details.items():
            with self.subTest(key=key):
                self.assertEqual(key, value)

    def test_new_page_show_correct_context(self):
        """Template new generated with correct context."""
        response = self.client_bob.get(NEW_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        edit_pattern = response.context.get('is_edit')
        self.assertEqual(edit_pattern, False)

    def test_post_edit_show_correct_context(self):
        """Template post_edit generated with correct context."""
        post = PostsViewsTests.post
        author = post.author.username
        post_edit_url = reverse('post_edit', args=[author, post.id])
        response = self.client_bob.get(post_edit_url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        edit_pattern = response.context.get('is_edit')
        self.assertEqual(edit_pattern, True)

    def test_post_show_correct_context(self):
        """"Template post generated with correct context."""
        post = PostsViewsTests.post
        post_url = reverse('post', args=[post.author.username, post.id])
        response = self.client_john.get(post_url)
        expected_page_details = {
            PostsViewsTests.post: response.context.get('post'),
            PostsViewsTests.posts_count: response.context.get('posts_count'),
        }
        for key, value in expected_page_details.items():
            with self.subTest(key=key):
                self.assertEqual(key, value)

    def test_homepage_show_correct_number_of_posts(self):
        """"Template homepage contains required amount of generated posts."""
        response = self.client_bob.get(INDEX_URL)
        self.assertEqual(len(response.context['page']), PER_PAGE)

    def test_group_page_show_correct_number_of_posts(self):
        """"Template for first test group contains only posts that belong
        to first group.
        """
        group_items = Group.objects.filter(slug='slug_one').count()
        group_url = reverse('group', args=['slug_one'])
        response = self.client_john.get(group_url)
        self.assertEqual(len(response.context['page']), group_items)
