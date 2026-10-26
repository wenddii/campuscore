from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from apps.students.models import Department
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

    def test_registration_requires_bank_number_and_book(self):
        data = {
            **self.common,
            "bank_account_number": "123456",
        }
        form = StudentRegistrationForm(data=data, files={})
        self.assertFalse(form.is_valid())
        self.assertIn("bank_book_photo", form.errors)

        form = StudentRegistrationForm(
            data=data,
            files={"bank_book_photo": image_upload("book.png")},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_registration_has_no_cafeteria_or_holder_name_fields(self):
        self.assertNotIn("student_type", StudentRegistrationForm.base_fields)
        self.assertNotIn("bank_account_name", StudentRegistrationForm.base_fields)
