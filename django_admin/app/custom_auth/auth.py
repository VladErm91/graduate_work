import logging
import uuid

import jwt
import requests
from custom_auth.enums import Roles
from custom_auth.models import User
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.core.cache import cache
from django.utils import timezone


class CustomBackend(BaseBackend):
    def decoded_token(self, access_token):
        """Decode the received token."""
        try:
            return jwt.decode(access_token, options={"verify_signature": False})
        except Exception as e:
            logging.error(f"Token decoding error: {e}")
            return None

    def cache_tokens(self, username, tokens):
        """
        Метод для сохранения токена в кэш
        """
        cache.set(f"tokens_{username}", tokens, timeout=3600)

    def get_cached_tokens(self, username):
        """
        Метод для получения токена из кэша
        """
        return cache.get(f"tokens_{username}")

    def get_request_id(self, request):
        # Получение X-Request-Id из заголовков запроса или генерация нового UUID
        return request.headers.get("X-Request-Id", str(uuid.uuid4()))

    def authenticate(self, request, username=None, password=None):
        payload = {"username": username, "password": password}
        url = settings.AUTH_API_LOGIN_URL
        request_id = self.get_request_id(request)
        try:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Request-Id": request_id,
            }
            response = requests.post(url, data=payload, headers=headers)
            response.raise_for_status()  # Raise error for bad responses
        except requests.exceptions.RequestException as e:
            logging.error(f"Auth service is not available: {e}")
            tokens = self.get_cached_tokens(username)
            if tokens:
                return self.authenticate_with_cached_tokens(username, tokens)
            return self.get_user_by_username(username)

        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")

        if not access_token or not refresh_token:
            logging.error("No tokens received from authentication service.")
            return None

        self.cache_tokens(
            username, {"access_token": access_token, "refresh_token": refresh_token}
        )

        # Декодирование access токена
        decoded_token = self.decoded_token(access_token=access_token)
        if not decoded_token:
            return None
        # print(decoded_token)

        user_id = decoded_token.get("id")
        user_login = decoded_token.get("login")
        first_name = decoded_token.get("first_name")
        last_name = decoded_token.get("last_name")
        roles = decoded_token.get("roles", [])

        try:
            user, created = User.objects.get_or_create(
                id=user_id,
                defaults={
                    "login": user_login,
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_admin": Roles.ADMIN in roles,
                    "is_active": True,
                    "created_at": timezone.now(),  # Ensure this is filled with aware datetime
                },
            )
            if created:
                user.last_login = timezone.now()  # Set last_login only on creation
            else:
                # Update the existing user's details
                user.login = (user_login,)
                user.first_name = first_name
                user.last_name = last_name
                user.is_admin = Roles.ADMIN in roles
                user.is_active = True
                user.last_login = (
                    timezone.now()
                )  # Update last_login to current time safely
                user.save()
        except Exception as e:
            logging.error(f"Error creating or updating user: {e}")
            return None

        return user

    def authenticate_with_cached_tokens(self, username, tokens):
        decoded_token = self.decoded_token(access_token=tokens["access_token"])
        if not decoded_token:
            return None

        user_id = decoded_token.get("id")
        user_login = decoded_token.get("login")
        first_name = decoded_token.get("first_name")
        last_name = decoded_token.get("last_name")
        roles = decoded_token.get("roles", [])

        try:
            user = User.objects.get(pk=user_id)
            user.login = (user_login,)
            user.first_name = first_name
            user.last_name = last_name
            user.is_admin = Roles.ADMIN in roles
            user.is_active = True
            user.last_login = timezone.now()  # Update last_login to current time safely
            user.save()
            return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def get_user_by_username(self, username):
        """
        Метод для поиска пользователя в базе данных, если токенов нет в кэше
        """
        try:
            return User.objects.get(login=username)
        except User.DoesNotExist:
            return None
