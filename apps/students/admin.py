from django.contrib import admin
from .models import Department, Student


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "program_duration",
    )

    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "student_id",
        "full_name",
        "department",
        "academic_year",
        "information_confirmed",
        "verification_status",
        "bank_details_status",
    )

    search_fields = (
        "student_id",
        "full_name",
    )

    list_filter = (
        "department",
        "academic_year",
        "information_confirmed",
        "verification_status",
        "bank_details_status",
    )

    ordering = (
        "department",
        "academic_year",
        "student_id",
    )

    fieldsets = (
        ("Student Information", {
            "fields": (
                "student_id",
                "full_name",
                "department",
                "academic_year",
            )
        }),
        ("Bank Details", {
            "fields": (
                "bank_account_number",
                "bank_book_photo",
                "bank_details_status",
            )
        }),
        ("Student Declaration", {
            "fields": (
                "information_confirmed",
                "confirmation_name",
                "confirmed_at",
            )
        }),
        ("Student Verification", {
            "fields": (
                "verification_status",
            )
        }),
        ("Record Information", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    readonly_fields = (
        "information_confirmed",
        "confirmation_name",
        "confirmed_at",
        "created_at",
        "updated_at",
    )
