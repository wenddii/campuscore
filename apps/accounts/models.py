from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Authentication model for the campus registration system.

    Business-specific student information will live in separate models.
    Access permissions will be configured as the application develops.
    """

    pass