from django.conf import settings
from django.db import models


class Registration(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class StudentStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="registrations",
    )

    academic_year = models.CharField(
        max_length=20,
        help_text="Academic year, for example 2026/2027.",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    student_status = models.CharField(
        max_length=10,
        choices=StudentStatus.choices,
        default=StudentStatus.ACTIVE,
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_registrations",
    )

    review_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "academic_year"],
                name="unique_student_registration_per_year",
            ),
        ]
        ordering = ["-academic_year", "student__student_id"]

    def __str__(self):
        return f"{self.student.student_id} - {self.academic_year}"