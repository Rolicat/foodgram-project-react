from django.db import models
from django.contrib.auth.models import AbstractUser
from users.validators import UsernameRegexValidator


class User(AbstractUser):
    username = models.CharField(
        'Имя пользователя',
        validators=(UsernameRegexValidator(),),
        max_length=150,
        unique=True,
        blank=False,
        null=False,
    )
    email = models.EmailField(
        'Электронная почта',
        max_length=254,
        unique=True,
        blank=False,
        null=False
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
        blank=False,
        null=False,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
        blank=False,
        null=False,
    )
    REQUIRED_FIELDS = ('username', )
    USERNAME_FIELD = 'email'

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return f'{self.username} {self.email}'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
        help_text='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор рецептов',
        help_text='Автор рецептов',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author',),
                name='user_not_equal_author',
            ),
        )

    def __str__(self) -> str:
        return (f'Пользователь {self.user.username} '
                f'следит за {self.author.username}'
                )
