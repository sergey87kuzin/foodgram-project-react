from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email), **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        return self.create_user(
            email=email, is_staff=True, password=password,
            **extra_fields
        )

    def all(self):
        return self.get_queryset()


class User(AbstractBaseUser):
    is_staff = models.BooleanField(default=False)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    first_name = models.CharField(max_length=150, verbose_name='first_name')
    last_name = models.CharField(max_length=150, verbose_name='last_name')
    username = models.CharField(max_length=150, unique=True,
                                verbose_name='username')
    password = models.CharField(max_length=150, verbose_name='password',
                                blank=True)

    objects = MyUserManager()

    USERNAME_FIELD = 'email'
    USER_ID_FIELD = 'id'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'password', 'username']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ('-id',)

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
