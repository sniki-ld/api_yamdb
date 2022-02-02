from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import send_mail
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# Создаем класс менеджера пользователей
class MyUserManager(BaseUserManager):
    """Create and save a user with the given username, email and password"""

    # Создаём базовый метод для создания пользователя
    def _create_user(self, username, email, password, **extra_fields):
        # Проверяем есть ли Email
        if not email:
            # Выводим сообщение в консоль
            raise ValueError('The given email must be set')
        # Проверяем есть ли логин
        if not username:
            # Выводим сообщение в консоль
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)  # предотвращение множественных регистраций
        username = self.model.normalize_username(username)
        # Создаем пользователя
        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )
        # Сохраняем пароль
        user.set_password(password)
        # Сохраняем всё остальное
        user.save(using=self._db)
        # Возвращаем пользователя
        return user

    # Создаем метод для создание обычного пользователя
    # def create_user(self, username, email, password=None, **extra_fields):
    #     extra_fields.setdefault('is_staff', False)
    #     extra_fields.setdefault('is_admin', False)
    #     # Возвращаем нового созданного пользователя
    #     return self._create_user(
    #         email, username, password, **extra_fields
    #     )
    def create_user(self, email, username, password=None, **extra_fields):
        # Возвращаем нового созданного пользователя
        return self._create_user(email, username, password, **extra_fields)

    # Создаем метод для создание админа сайта
    # def create_superuser(self, username, email, password=None, **extra_fields):
    #     extra_fields.setdefault('is_staff', True)
    #     extra_fields.setdefault('is_admin', True)
    #     if extra_fields.get('is_staff') is not True:
    #         raise ValueError('Superuser must have is_staff=True.')
    #     if extra_fields.get('is_admin') is not True:
    #         raise ValueError('Superuser must have is_admin=True.')
    #     # Возвращаем нового созданного админа
    #     return self._create_user(
    #         username, email, password, **extra_fields
    #     )

    def create_superuser(self, email, password=None, **extra_fields):
        user = self.create_user(
            email,
            password=password,
            **extra_fields
        )
        user.role = 'admin'
        user.is_admin = True
        user.save(using=self._db)
        return user


# Создаём свою модель User, наследуем от AbstractBaseUser
class User(AbstractBaseUser):
    """Model representing users."""
    USER_ROLES = (
        ('user', 'user'),
        ('moderator', 'moderator'),
        ('admin', 'admin'),
    )

    username_validator = UnicodeUsernameValidator()  # Letters, digits and @/./+/-/_ only.

    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
        # verbose_name='Login'
    )  # Логин
    email = models.EmailField(max_length=254, unique=True, verbose_name='Email')
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    bio = models.TextField(
        max_length=300,
        null=True,
        blank=True,
        help_text='About myself'
    )
    role = models.CharField(max_length=10,
                            choices=USER_ROLES,
                            default='user',
                            verbose_name='Role')
    is_active = models.BooleanField(default=True)  # Статус активации
    is_staff = models.BooleanField(default=False)  # Статус админа

    USERNAME_FIELD = 'email'  # Идентификатор для обращения
    REQUIRED_FIELDS = ['username']  # Список имён полей для Superuser

    # Сообщает Django, что класс UserManager, определенный выше,
    # должен управлять объектами этого типа.
    objects = MyUserManager()

    # Метод для отображения в админ панели
    def __str__(self):
        return self.email

    # Посылает email пользователю. Если from_email равен None, Django использует настройку DEFAULT_FROM_EMAIL.
    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)


class Category(models.Model):
    """Model representing categories (types) of works."""
    name = models.CharField(max_length=256, verbose_name='Category', help_text='Select a category for this work')
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Genre(models.Model):
    """Model representing genres of works."""
    name = models.CharField(max_length=256, verbose_name='Genre', help_text='Select a genre for this work')
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Title(models.Model):
    """Specific work to which they write reviews."""
    name = models.CharField(max_length=256,
                            verbose_name='Title')
    year = models.IntegerField(help_text='Select the year of release of the work')
    category = models.ForeignKey(Category,
                                 related_name='titles',
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 help_text='Select a category for this work')
    genre = models.ManyToManyField(Genre,
                                   related_name='genres',
                                   # on_delete=models.SET_NULL,
                                   # null=True,
                                   help_text='Select a genre for this work')
    description = models.TextField(blank=True, null=True,
                                   help_text='Enter a brief description of the work')

    def __str__(self):
        return self.name


class Review(models.Model):
    """User reviews for works."""
    text = models.TextField(verbose_name='Text')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Author')
    score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name='Rating')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    db_index=True,
                                    verbose_name='Publication date')

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.title.name, self.text


class Comments(models.Model):
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, related_name='reviews')
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(verbose_name='Текст')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="comments",
        verbose_name='Author')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    db_index=True,
                                    verbose_name='Publication date')

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text
