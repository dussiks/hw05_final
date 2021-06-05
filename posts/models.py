from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.query import QuerySet


User = get_user_model()


class Group(models.Model):
    """Define elements for each group and their appearance."""
    title = models.CharField(
        verbose_name='название',
        max_length=200,
        help_text='введите название группы.',
    )
    description = models.TextField(verbose_name='описание')
    slug = models.SlugField(
        verbose_name='слаг',
        unique=True,
        help_text=('Слаг должен быть уникальным. Используйте только '
                   'латиницу, цифры, дефисы и знаки подчёркивания.'),
    )

    def __str__(self):
        return self.title


class PostManager(models.Manager):
    def __getattr__(self, attr, *args):
        try:
            return getattr(self.__class__, attr, *args)
        except AttributeError:
            # don't delegate internal methods to the queryset
            if attr.startswith('__') and attr.endswith('__'):
                raise
            return getattr(self.get_query_set(), attr, *args)

    def optimized(self):
        return self.select_related('author', 'group').all()


class Post(models.Model):
    text = models.TextField(
        verbose_name='текст',
        help_text='Напишите текст Вашей новой записи. Это обязательно.',
    )
    pub_date = models.DateTimeField("дата публикации", auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    group = models.ForeignKey(
        Group,
        verbose_name='группа',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts",
        help_text='Выберите группу. Это необязательно.',
    )
    image = models.ImageField(upload_to="posts/", blank=True, null=True,)
    objects = PostManager()


    class Meta:
        ordering = ("-pub_date",)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    text = models.TextField(
        null=False,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta():
        ordering = ("created",)

    def __str__(self):
        return self.text[:20]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        related_name='following',
    )
