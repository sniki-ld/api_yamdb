from django.db import models  # Подключаем работу с моделями
# Подключаем классы для создания пользователей
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .validators import validate_username


class CustomUserManager(BaseUserManager):
    """Кастомный класс для создания новых пользователей."""

    # Переопределяем методы, которые отвечают за создание пользователя.
    def create_user(self, email, username, password=None):
        """
        Создаем и сохраняем пользователя с заданным именем пользователя
         и адресом электронной почты
        """
        # Проверяем есть ли Email
        if not email:
            raise ValueError('Адрес электронной почты должен быть установлен')
        # Проверяем есть ли логин
        if not username:
            raise ValueError('Имя пользователя должно быть установлено')
        # Создаем пользователя
        user = self.model(
            email=self.normalize_email(email),  # предотвращение множественных регистраций
            username=self.model.normalize_username(username),
        )
        # Сохраняем пароль
        user.set_password(password)
        # Сохраняем всё остальное
        user.save(using=self._db)
        # Возвращаем пользователя
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=self.model.normalize_username(username),
        )
        user.is_admin = True
        user.is_staff = True  # имеет ли пользователь доступ к панели администратора или нет.
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser):
    """Описываем кастомную модель пользователя."""
    ROLE_CHOICES = (
        ('user', 'Аутентифицированный пользователь'),
        ('moderator', 'Модератор'),
        ('admin', 'Администратор')
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Email'
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[validate_username]
    )
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    date_joined = models.DateTimeField(  # Дата и время, когда была создана учетная запись.
        # Устанавливается на текущую дату/время по умолчанию при создании учетной записи.
        auto_now_add=True,
        verbose_name='date joined'
    )
    last_login = models.DateTimeField(  # Дата и время последнего входа пользователя в систему.
        auto_now=True,
        verbose_name='last login'
    )
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # следует ли считать эту учетную запись активной.
    is_staff = models.BooleanField(default=False)  # может ли этот пользователь получить доступ к сайту администратора.
    is_superuser = models.BooleanField(default=False)  # у пользователя есть все разрешения без их явного назначения.

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user'
    )
    bio = models.TextField(
        max_length=300,
        null=True,
        blank=True,
        help_text='About myself'
    )

    USERNAME_FIELD = 'username'  # уникальный идентифик. пользователя, вместе с паролем, используется при авторизации.
    REQUIRED_FIELDS = ['email']  # список полей, кот.нужно ввести при созд. пользователя ч/команду createsuperuser

    # Сообщает Django, что класс UserManager, определенный выше,
    # должен управлять объектами этого типа.
    objects = CustomUserManager()

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):  # Возвращает True если пользователь имеет указанное право доступа,
        # где право указывает в формате "<app label>.<permission codename>".
        # (смотрите раздел Права пользователя ниже). Если пользователь неактивный, метод всегда возвращает False.
        return self.is_admin

    def has_module_perms(self, app_label):  # Возвращает True если пользователь имеет хотя бы одно право доступа
        # для указанного приложения. Если пользователь неактивный, метод вернет False.
        return True
