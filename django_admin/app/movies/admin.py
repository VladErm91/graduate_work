from django.contrib import admin
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _

from .models import Filmwork, Genre, GenreFilmwork, Person, PersonFilmwork


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "created", "modified")
    ordering = ("name",)
    search_fields = ("name", "description", "id")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "created", "modified")
    ordering = ("full_name",)
    search_fields = ("full_name", "id")


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork
    autocomplete_fields = ("genre",)
    extra = 1
    verbose_name = _("genre")
    verbose_name_plural = _("genres")


class PersonFilmworkInline(admin.TabularInline):
    model = PersonFilmwork
    autocomplete_fields = (
        "person",
        "film_work",
    )
    verbose_name = _("person")
    verbose_name_plural = _("persons")


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):

    inlines = (GenreFilmworkInline, PersonFilmworkInline)

    list_display = (
        "title",
        "type",
        "creation_date",
        "rating",
        "get_genres",
    )

    @admin.display(description=_("genres"))
    def get_genres(self, genres):
        return ",".join([genre.name for genre in genres.genres.all()])

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related(
            Prefetch("genres", queryset=Genre.objects.order_by("name"))
        )

    list_filter = ("type", "genres")
    search_fields = ("title", "description", "id")
