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
        "student_type",
        "department",
        "academic_year",
        "information_confirmed",
        "verification_status",
        "bank_details_status",
        "cafeteria_exempt",
    )

    search_fields = (
        "student_id",
        "full_name",
    )

    list_filter = (
        "student_type",
        "department",
        "academic_year",
        "information_confirmed",
        "verification_status",
        "bank_details_status",
        "cafeteria_exempt",
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
                "photo",
                "student_type",
                "department",
                "academic_year",
            )
        }),
        ("Bank Details", {
            "fields": (
                "bank_account_name",
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
                "cafeteria_exempt",
                "qr_code",
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
        "qr_code",
        "created_at",
        "updated_at",
    )
