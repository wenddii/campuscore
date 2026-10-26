from django.urls import path
from . import views

app_name = "students"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("students/register/", views.register_student, name="register"),
    path("students/<int:student_id>/", views.student_detail, name="detail"),
    path("students/<int:student_id>/edit/", views.edit_student, name="edit"),
    path("students/<int:student_id>/approve/", views.approve_student, name="approve"),
    path("students/<int:student_id>/verify/", views.verify_student, name="verify"),
    path("students/<int:student_id>/reject/", views.reject_student, name="reject"),
    path("students/<int:student_id>/bank/<str:decision>/", views.review_bank, name="review_bank"),
    path("students/<int:student_id>/status/", views.update_verification_status, name="update_status"),
    path("students/<int:student_id>/bank-status/", views.update_bank_status, name="update_bank_status"),
]
