from django.core.exceptions import ValidationError
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    program_duration = models.PositiveSmallIntegerField(
        help_text="Number of academic years in this program."
    )

    def __str__(self):
        return self.name


class Student(models.Model):

    class StudentType(models.TextChoices):
        CAFETERIA = "cafeteria", "Cafeteria"
        NON_CAFETERIA = "non_cafeteria", "Non-Cafeteria"

    class AcademicYear(models.TextChoices):
        YEAR_1 = "1", "Year 1"
        YEAR_2 = "2", "Year 2"
        YEAR_3 = "3", "Year 3"
        YEAR_4 = "4", "Year 4"
        YEAR_5 = "5", "Year 5"
        YEAR_6 = "6", "Year 6"
        OTHER = "other", "Other / Special Case"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending Verification"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    class BankDetailsStatus(models.TextChoices):
        PENDING = "pending", "Pending Review"
        VERIFIED = "verified", "Bank Details Verified"
        REJECTED = "rejected", "Bank Details Rejected"

    student_id = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=150)
    cafeteria_exempt = models.BooleanField(default=False)
    photo = models.ImageField(
        upload_to="student_photos/",
        blank=True,
    )

    qr_code = models.ImageField(
        upload_to="student_qr_codes/",
        blank=True,
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="students",
    )

    academic_year = models.CharField(
        max_length=10,
        choices=AcademicYear.choices,
    )

    student_type = models.CharField(
        max_length=20,
        choices=StudentType.choices,
    )

    bank_account_name = models.CharField(
        max_length=150,
        blank=True,
    )

    bank_account_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )

    bank_book_photo = models.ImageField(
        upload_to="bank_book_photos/",
        blank=True,
    )

    verification_status = models.CharField(
        max_length=10,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )

    bank_details_status = models.CharField(
        max_length=10,
        choices=BankDetailsStatus.choices,
        default=BankDetailsStatus.PENDING,
    )

    confirmation_name = models.CharField(
        max_length=150,
        blank=True,
    )

    information_confirmed = models.BooleanField(
        default=False,
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()

        errors = {}

        # Validate the student's academic year.
        if self.department_id and self.academic_year:
            if self.academic_year != self.AcademicYear.OTHER:
                year = int(self.academic_year)

                if year > self.department.program_duration:
                    errors["academic_year"] = (
                        f"{self.department.name} has a "
                        f"{self.department.program_duration}-year program. "
                        f"Year {year} is not valid for this department."
                    )

        # Non-cafeteria students must submit bank details.
        if self.student_type == self.StudentType.NON_CAFETERIA:
            if not self.bank_account_number or not self.bank_account_number.strip():
                errors["bank_account_number"] = (
                    "Bank account number is required "
                    "for non-cafeteria students."
                )

            if not self.bank_book_photo:
                errors["bank_book_photo"] = (
                    "Bank book photo is required "
                    "for non-cafeteria students."
                )

        # Cafeteria students do not submit bank details.
        elif self.student_type == self.StudentType.CAFETERIA:
            if (
                self.bank_account_name.strip()
                or self.bank_account_number
                or self.bank_book_photo
            ):
                errors["student_type"] = (
                    "Cafeteria students should not submit bank details."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"
