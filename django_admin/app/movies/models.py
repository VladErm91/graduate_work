from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .mixins import TimeStampedMixin, UUIDMixin
from .storage import CustomStorage


class Filmwork(UUIDMixin, TimeStampedMixin):
    class FilmTypes(models.TextChoices):
        movies = "MOVIES"
        tv_show = "TV Show"

    title = models.TextField(_("title"), null=False, blank=False, max_length=255)
    description = models.TextField(_("description"), null=True, blank=True)
    creation_date = models.DateTimeField(
        _("creation date"),
        null=True,
        auto_now_add=True,
    )
    rating = models.FloatField(
        _("rating"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    type = models.CharField(
        _("type"),
        max_length=35,
        choices=FilmTypes.choices,
        default=FilmTypes.movies,
    )
    genres = models.ManyToManyField("Genre", through="GenreFilmwork")
    person = models.ManyToManyField("Person", through="PersonFilmwork")
    file = models.FileField(_("file"), storage=CustomStorage, null=True)

    class Meta:
        db_table = 'content"."film_work'
        verbose_name = _("movie")
        verbose_name_plural = _("movies")

    def __str__(self):
        return self.title


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField("description", null=True, blank=True)

    class Meta:
        db_table = 'content"."genre'
        verbose_name = _("genre")
        verbose_name_plural = _("genres")

    def __str__(self):
        return self.name


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content"."genre_film_work'

    def __str__(self):
        return ""


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField(_("full name"), blank=True)

    class Meta:
        db_table = 'content"."person'
        verbose_name = _("person")
        verbose_name_plural = _("persons")

    def __str__(self):
        return self.full_name


class PersonFilmwork(UUIDMixin):
    class Roles(models.TextChoices):
        actor = "actor", _("actor")
        writer = "writer", _("writer")
        director = "director", _("director")

    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.TextField(_("role"), choices=Roles.choices, max_length=12, null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'content"."person_film_work'

    def __str__(self):
        return ""
