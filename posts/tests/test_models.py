from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post, Comment


User = get_user_model()
SLUG = 'test_slug'


class PostCommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        author = User.objects.create(username='Vova')
        cls.post = Post.objects.create(
            author=author,
            text='Тестовый текст',
        )
        cls.comment = Comment.objects.create(
            author=author,
            post=cls.post,
            text='Тестовый комментарий для проверки',
        )

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
