from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from apps.students.models import Department, Student
from .forms import StudentRegistrationForm


def image_upload(name="image.png"):
    image = Image.new("RGB", (10, 10), "white")
    stream = BytesIO()
    image.save(stream, format="PNG")
    return SimpleUploadedFile(name, stream.getvalue(), content_type="image/png")


class StudentRegistrationFormTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="Computer Science", program_duration=4
        )
        self.common = {
            "student_id": "STU-001",
            "full_name": "Test Student",
            "department": self.department.pk,
            "academic_year": "1",
            "confirmation_name": "Test Student",
            "information_confirmed": "on",
        }

    def test_cafeteria_requires_photo_and_ignores_no_bank_fields(self):
        data = {**self.common, "student_type": Student.StudentType.CAFETERIA}
        form = StudentRegistrationForm(data=data, files={})
        self.assertFalse(form.is_valid())
        self.assertIn("photo", form.errors)
        self.assertNotIn("bank_account_name", form.fields)

        form = StudentRegistrationForm(
            data=data,
            files={"photo": image_upload()},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_non_cafeteria_requires_bank_number_and_book_without_photo(self):
        data = {
            **self.common,
            "student_id": "STU-002",
            "student_type": Student.StudentType.NON_CAFETERIA,
            "bank_account_number": "123456",
        }
        form = StudentRegistrationForm(data=data, files={})
        self.assertFalse(form.is_valid())
        self.assertIn("bank_book_photo", form.errors)
        self.assertNotIn("photo", form.errors)
        self.assertNotIn("bank_account_name", form.fields)

        form = StudentRegistrationForm(
            data=data,
            files={"bank_book_photo": image_upload("book.png")},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_non_cafeteria_photo_submission_is_rejected(self):
        data = {
            **self.common,
            "student_id": "STU-003",
            "student_type": Student.StudentType.NON_CAFETERIA,
            "bank_account_number": "123457",
        }
        form = StudentRegistrationForm(
            data=data,
            files={
                "photo": image_upload(),
                "bank_book_photo": image_upload("book.png"),
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("student_type", form.errors)
