import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class MyUserManager(BaseUserManager):
    def create_user(self, login, password=None):
        if not login:
            raise ValueError("Users must have an email address")

        user = self.model(login=self.normalize_email(login))
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login, password=None):
        user = self.create_user(login, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login = models.EmailField(_("login"), max_length=255, unique=True)
    email = models.EmailField(_("email address"), max_length=255, unique=True)
    password = models.CharField(_("password"), max_length=255)
    first_name = models.CharField(_("first name"), max_length=50, blank=True, null=True)
    last_name = models.CharField(_("last name"), max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    last_login = models.DateTimeField(_("last login"), blank=True, null=True)

    # строка с именем поля модели, которая используется в качестве уникального идентификатора
    USERNAME_FIELD = "login"

    # менеджер модели
    objects = MyUserManager()

    class Meta:
        db_table = "users"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.email} {self.id}"

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
