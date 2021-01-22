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
        cls.user_alf = User.objects.create(username='alf')
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
        cls.posts_count = cls.user_bob.posts.count()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        user_bob = PostsViewsTests.user_bob
        user_john = PostsViewsTests.user_john
        user_alf = PostsViewsTests.user_alf
        self.guest_client = Client()
        self.client_bob = Client()
        self.client_john = Client()
        self.client_alf = Client()
        self.client_bob.force_login(user_bob)
        self.client_john.force_login(user_john)
        self.client_alf.force_login(user_alf)
        self.follow = Follow.objects.create(
            user=user_john,
            author=user_bob,
        )
        self.comment = Comment.objects.create(
            author=user_john,
            post=PostsViewsTests.post,
            text='Тестовый комментарий Джона на пост Боба.'
        )

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
        post = PostsViewsTests.post
        author = post.author
        response = self.client_john.get(reverse('profile',
                                                args=[author.username]))
        expected_page_details = {
            post: response.context.get('page')[0],
            PostsViewsTests.posts_count: response.context.get('posts_count'),
            author: response.context.get('author'),
            author.following.count(): response.context.get('followers_count'),
            author.follower.count(): response.context.get('followings_count'),
            True: response.context.get('following'),
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
        edit_url = reverse('post_edit', args=[post.author.username, post.id])
        response = self.client_bob.get(edit_url)
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
        author = post.author
        post_url = reverse('post', args=[author.username, post.id])
        response = self.client_john.get(post_url)
        expected_page_details = {
            post: response.context.get('post'),
            author: response.context.get('author'),
            PostsViewsTests.posts_count: response.context.get('posts_count'),
            author.following.count(): response.context.get('followers_count'),
            author.follower.count(): response.context.get('followings_count'),
        }
        for key, value in expected_page_details.items():
            with self.subTest(key=key):
                self.assertEqual(key, value)
        form_field = response.context.get('form').fields.get('text')
        self.assertIsInstance(form_field, forms.fields.CharField)

    def test_404_error_show_correct_context(self):
        incorrect_url = '/wrong_address/'
        response = self.guest_client.get(incorrect_url)
        actual = response.context.get('path')
        self.assertEqual(actual, incorrect_url)
        self.assertEqual(response.status_code, 404)

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

    def test_user_follow_profile_author(self):
        """Correct Follow object created between user and profile author."""
        post = PostsViewsTests.post
        author = post.author
        user = PostsViewsTests.user_john
        follow_url = reverse('profile_follow', args=[author.username])
        Follow.objects.all().delete()
        self.client_john.get(follow_url)
        exist_answer = Follow.objects.filter(user=user, author=author).exists()
        self.assertEqual(exist_answer, True)

    def test_user_unfollow_profile_author(self):
        """After calling unfollow user stops following profile author."""
        post = PostsViewsTests.post
        author = post.author
        user = PostsViewsTests.user_john
        follow_url = reverse('profile_follow', args=[author.username])
        unfollow_url = reverse('profile_unfollow', args=[author.username])
        Follow.objects.all().delete()
        self.client_john.get(follow_url)
        self.client_john.get(follow_url)
        exist_answer = Follow.objects.filter(user=user, author=author).exists()
        self.assertEqual(exist_answer, True)
        self.client_john.get(unfollow_url)
        exist_answer = Follow.objects.filter(user=user, author=author).exists()
        self.assertEqual(exist_answer, False)

    def test_new_post_seen_only_for_followers(self):
        """New post created by author seen only for followers and not seen
        on user's page who is not follower.
        """
        follower = PostsViewsTests.user_bob
        author = PostsViewsTests.user_alf
        Follow.objects.filter(author=author).delete()
        Follow.objects.create(user=follower, author=author)
        new_post = Post.objects.create(
            text='Test Alf special post',
            author=author,
        )
        response_follower = self.client_bob.get(FOLLOW_URL)
        response_not_follower = self.client_john.get(FOLLOW_URL)
        self.assertIn(new_post, response_follower.context['page'])
        self.assertNotIn(new_post, response_not_follower.context['page'])

    def test_profile_author_can_not_follow_himself(self):
        """Profile author can not be follower of himself."""
        post = PostsViewsTests.post
        author = post.author
        follow_url = reverse('profile_follow', args=[author.username])
        Follow.objects.all().delete()
        self.client_bob.get(follow_url)
        user = PostsViewsTests.user_bob
        exist_answer = Follow.objects.filter(user=user, author=author).exists()
        self.assertEqual(exist_answer, False)
