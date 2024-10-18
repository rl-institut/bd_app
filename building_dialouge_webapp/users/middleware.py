from allauth.account.models import EmailAddress
from allauth.account.utils import perform_login
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.core.exceptions import ImproperlyConfigured
from django.utils.deprecation import MiddlewareMixin

DEFAULT_USERNAME = "default"


class AlwaysAuthenticateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def login_dummy_user(request):
        if request.user.is_authenticated:
            return request

        # Get the user model (usually this is the `User` model from `django.contrib.auth.models`)
        User = get_user_model()

        # Create a dummy user if it doesn't exist already
        email = "dummyuser@example.com"
        username = "dummyuser"
        password = "dummypassword123"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
            },
        )

        # If the user is created for the first time, set a password
        if created:
            user.set_password(password)
            user.save()

            # Associate email address (this is important if you're using allauth's email confirmation)
            EmailAddress.objects.create(
                user=user,
                email=email,
                verified=True,
                primary=True,
            )

        # Log in the dummy user
        perform_login(
            request,
            user,
            email_verification=settings.ACCOUNT_EMAIL_VERIFICATION,
        )
        return request

    def __call__(self, request):
        request = self.login_dummy_user(request)
        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response


class AlwaysAuthenticatedMiddleware(MiddlewareMixin):
    """
    Ensures that the request has an authenticated user.

    If the request doesn't have an authenticated user, it logs in a default
    user. If the default user doesn't exist, it is created.

    Will raise an ImproperlyConfiguredException when DEBUG=False, unless
    ALWAYS_AUTHENTICATED_DEBUG_ONLY is set to False.

    This middleware reads these settings:
    * ALWAYS_AUTHENTICATED_USERNAME (string):
      the name of the default user, defaults to `'user'`.
    * ALWAYS_AUTHENTICATED_USER_DEFAULTS (dict):
      additional default values to set when creating the user.
    * ALWAYS_AUTHENTICATED_DEBUG_ONLY:
      Set to `False` to allow running with DEBUG=False.
    """

    def __init__(self, *args, **kwargs):
        self.username = getattr(settings, "ALWAYS_AUTHENTICATED_USERNAME", "user")
        self.defaults = getattr(settings, "ALWAYS_AUTHENTICATED_USER_DEFAULTS", {})
        if not settings.DEBUG and getattr(
            settings,
            "ALWAYS_AUTHENTICATED_DEBUG_ONLY",
            True,
        ):
            raise ImproperlyConfigured(
                "DEBUG=%s, but AlwaysAuthenticatedMiddleware is configured to "
                "only run in debug mode.\n"
                "Remove AlwaysAuthenticatedMiddleware from "
                "MIDDLEWARE/MIDDLEWARE_CLASSES or set "
                "ALWAYS_AUTHENTICATED_DEBUG_ONLY to False." % settings.DEBUG,
            )
        super(AlwaysAuthenticatedMiddleware, self).__init__(*args, **kwargs)

    def process_request(self, request):
        if not request.user.is_authenticated:
            user, created = User.objects.get_or_create(
                username=self.username,
                defaults=self.defaults,
            )

            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(request, user)
