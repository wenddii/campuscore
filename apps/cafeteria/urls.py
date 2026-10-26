from django.urls import path
from . import views

app_name = "cafeteria"

urlpatterns = [
    path("scan/", views.scan_page, name="scan"),
]
