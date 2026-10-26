from django.contrib import admin
from .models import Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "academic_year",
        "status",
        "student_status",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
    )

    list_filter = (
        "academic_year",
        "status",
        "student_status",
    )

    search_fields = (
        "student__student_id",
        "student__full_name",
    )

    readonly_fields = (
        "submitted_at",
        "reviewed_at",
        "created_at",
        "updated_at",
    )