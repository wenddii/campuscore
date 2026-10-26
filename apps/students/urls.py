from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("students/<int:student_id>/", views.student_detail, name="detail"),
    path("students/<int:student_id>/verify/", views.verify_student, name="verify"),
    path("students/<int:student_id>/reject/", views.reject_student, name="reject"),
    path("students/<int:student_id>/bank/<str:decision>/", views.review_bank, name="review_bank"),
    path("students/<int:student_id>/exempt/", views.toggle_exempt, name="toggle_exempt"),
]
