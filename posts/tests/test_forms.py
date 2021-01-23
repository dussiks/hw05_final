import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post


User = get_user_model()
SLUG = 'slug_one'
IMG = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
       b'\x01\x00\x80\x00\x00\x00\x00\x00'
       b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
       b'\x00\x00\x00\x2C\x00\x00\x00\x00'
       b'\x02\x00\x01\x00\x00\x02\x02\x0C'
       b'\x0A\x00\x3B')


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user_bob = User.objects.create(username='bob')
        cls.user_john = User.objects.create(username='john')
        cls.group = Group.objects.create(
            title='First test group title',
            description='About first test group',
            slug=SLUG,
        )
        Post.objects.create(
            text='Test first post',
            author=cls.user_bob,
            group=Group.objects.get(slug=SLUG),
        )
        cls.post = Post.objects.create(
            text='Test second post',
            author=cls.user_bob,
        )
        cls.post_form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client_bob = Client()
        self.client_john = Client()
        self.client_bob.force_login(PostFormTests.user_bob)
        self.client_john.force_login(PostFormTests.user_john)

    def test_create_post(self):
        """Valid form create correct post in choosen group."""
        all_posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=IMG,
            content_type='image/gif'
        )
        form_data = {
            'group': PostFormTests.group.id,
            'text': 'Test third post from form',
            'image': uploaded,
        }
        response = self.client_bob.post(
            reverse('new_post'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), all_posts_count + 1)
        new_post = Post.objects.get(text__icontains='post from form')
        answer = self.client_bob.get(reverse('group', args=[SLUG]))
        last_group_post = answer.context.get('page')[0]
        self.assertEqual(last_group_post, new_post)

    def test_post_text_field_help_text(self):
        """help-text for post form fields are written as desired."""
        text_help_text = PostFormTests.post_form.fields['text'].help_text
        self.assertEqual(
            text_help_text,
            'Напишите текст Вашей новой записи. Это обязательно.')

    def test_post_group_field_help_text(self):
        """help-text for group form fields are written as desired."""
        group_help_text = PostFormTests.post_form.fields['group'].help_text
        self.assertEqual(
            group_help_text,
            'Выберите группу. Это необязательно.')

    def test_cannot_create_post_without_required_field(self):
        """New post not created if required fields are not filled in form."""
        all_posts_count = Post.objects.count()
        form_data = {
            'group': PostFormTests.group.id,
        }
        response = self.client_bob.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), all_posts_count)
        self.assertEqual(response.status_code, 200)

    def test_post_edit_form_changes_current_post(self):
        """Valid form changes text in post and save it."""
        post = PostFormTests.post
        form_data = {
            'text': 'Edited second post',
        }
        response = self.client_bob.post(
            reverse('post_edit', args=[post.author.username, post.id]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('post', args=[post.author.username, post.id])
        )
        self.assertContains(response, 'Edited')
        self.assertEqual(response.status_code, 200)

    def test_create_comment(self):
        """Valid form create correct comment in choosen post."""
        post = PostFormTests.post
        post_comments_count = post.comments.count()
        form_data = {
            'text': 'Test comment in second post from form',
        }
        response = self.client_john.post(
            reverse('add_comment', args=[post.author.username, post.id]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('post', args=[post.author.username, post.id])
        )
        self.assertEqual(post.comments.count(), post_comments_count + 1)
        self.assertContains(response, 'Test comment in second')
        self.assertEqual(response.status_code, 200)

    def test_cannot_create_comment_without_required_field(self):
        """New comment not created if required field is not filled in form."""
        post = PostFormTests.post
        post_comments_count = post.comments.count()
        response = self.client_john.post(
            reverse('add_comment', args=[post.author.username, post.id]),
            data={},
            follow=True,
        )
        self.assertEqual(post.comments.count(), post_comments_count)
        self.assertEqual(response.status_code, 200)
