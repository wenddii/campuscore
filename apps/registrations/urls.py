from django.urls import path
from . import views

app_name = "registrations"

urlpatterns = [
    path("", views.register_student, name="register"),
    path("check/", views.lookup_submission, name="lookup"),
    path("status/", views.submission_status, name="status"),
]
