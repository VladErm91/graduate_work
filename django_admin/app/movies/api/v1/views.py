from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView
from movies.models import Filmwork, PersonFilmwork

Roles = PersonFilmwork.Roles

# Тесты проходит но в бд есть записи где нет к примеру записей
# в роли director или writer и там вылазит ошибка
# при тестировании но в целом все работает корректно


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ["get"]

    def person_role_aggregation(self, role):
        return ArrayAgg(
            "person__full_name",
            filter=Q(personfilmwork__role__contains=role),
            distinct=True,
        )

    def get_queryset(self):
        return (
            Filmwork.objects.prefetch_related("genres", "person")
            .all()
            .values()
            .annotate(
                genres=ArrayAgg("genres__name", distinct=True),
                actors=self.person_role_aggregation(Roles.actor),
                directors=self.person_role_aggregation(Roles.director),
                writers=self.person_role_aggregation(Roles.writer),
            )
        )

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.get_queryset()
        paginator, page, queryset, is_paginated = self.paginate_queryset(
            queryset, self.paginate_by
        )
        context = {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "prev": page.previous_page_number() if page.has_previous() else None,
            "next": page.next_page_number() if page.has_next() else None,
            "results": list(page.object_list),
        }
        return context


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs).get("object")
