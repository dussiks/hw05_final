import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post, Comment


User = get_user_model()
SLUG = 'test_slug'
IMG = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
       b'\x01\x00\x80\x00\x00\x00\x00\x00'
       b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
       b'\x00\x00\x00\x2C\x00\x00\x00\x00'
       b'\x02\x00\x01\x00\x00\x02\x02\x0C'
       b'\x0A\x00\x3B')


class PostCommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        author = User.objects.create(username='Vova')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=IMG,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=author,
            text='Тестовый текст',
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            author=author,
            post=cls.post,
            text='Тестовый комментарий для проверки',
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_verbose_name(self):
        """Post's verbose_name field content equals with desired."""
        post = PostCommentModelTest.post
        field_verboses = {
            'text': 'текст',
            'group': 'группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """Post's help_text field content equals with desired."""
        post = PostCommentModelTest.post
        field_help_texts = {
            'text': 'Напишите текст Вашей новой записи. Это обязательно.',
            'group': 'Выберите группу. Это необязательно.',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_post_name_is_text_field(self):
        """In __str__ field of post object written value of
        post.text[:15] field.
        """
        post = PostCommentModelTest.post
        expected_post_name = post.text[:15]
        self.assertEqual(expected_post_name, str(post))

    def test_comment_name_is_text_field(self):
        """In __str__ field of comment object written value of
        post.text[:20] field.
        """
        comment = PostCommentModelTest.comment
        expected_comment_name = comment.text[:20]
        self.assertEqual(expected_comment_name, str(comment))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Group test title',
            description='Описание тестовой группы',
            slug=SLUG,
        )

    def test_verbose_name(self):
        """verbose_name field content equals with desired."""
        group = GroupModelTest.group
        field_verboses = {
            'title': 'название',
            'description': 'описание',
            'slug': 'слаг',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text field content equals with desired."""
        group = GroupModelTest.group
        field_help_texts = {
            'title': 'введите название группы.',
            'slug': ('Слаг должен быть уникальным. Используйте только '
                     'латиницу, цифры, дефисы и знаки подчёркивания.')
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).help_text, expected)

    def test_group_name_is_title_field(self):
        """
        In __str__ field of group object written value of group.title field.
        """
        expected_object_name = GroupModelTest.group.title
        self.assertEqual(expected_object_name, str(GroupModelTest.group))
