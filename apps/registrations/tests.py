from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase
from PIL import Image

from apps.students.models import Department, Student
from .forms import StudentRegistrationForm
from .models import Registration, RegistrationSettings


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
            "section": "A",
            "confirmation_name": "Test Student",
            "information_confirmed": "on",
        }

    def test_registration_requires_section(self):
        data = {
            **self.common,
            "bank_account_number": "123456",
            "section": "",
        }
        form = StudentRegistrationForm(
            data=data,
            files={"bank_book_photo": image_upload("book.png")},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("section", form.errors)

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


class RegistrationSeasonTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="Computer Science",
            program_duration=4,
        )
        self.data = {
            "student_id": "STU-001",
            "full_name": "Test Student",
            "department": self.department.pk,
            "academic_year": "1",
            "section": "A",
            "bank_account_number": "001234",
            "confirmation_name": "Test Student",
            "information_confirmed": "on",
            "bank_book_photo": image_upload("book.png"),
        }

    def test_closed_registration_blocks_get_and_post(self):
        RegistrationSettings.objects.create(registration_open=False)

        get_response = self.client.get("/register/")
        post_response = self.client.post("/register/", self.data)

        self.assertEqual(get_response.status_code, 403)
        self.assertContains(
            get_response,
            "Registration is currently closed. Please contact the administration if you need assistance.",
            status_code=403,
        )
        self.assertEqual(post_response.status_code, 403)
        self.assertFalse(Registration.objects.exists())

    def test_open_registration_allows_submission(self):
        response = self.client.post("/register/", self.data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Registration.objects.filter(student__student_id="STU-001").exists())

    def test_student_registration_page_has_no_dashboard_navigation(self):
        response = self.client.get("/register/")
        self.assertNotContains(response, ">Dashboard</a>")
        self.assertNotContains(response, "Owner login")

        student_user = get_user_model().objects.create_user(
            username="student-user",
            password="student-password",
            is_staff=False,
        )
        self.client.force_login(student_user)

        response = self.client.get("/register/")

        self.assertNotContains(response, ">Dashboard</a>")
        self.assertNotContains(response, "Owner login")

    def test_registration_page_has_check_information_button(self):
        response = self.client.get("/register/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Already submitted? Check your information")

    def test_lookup_page_has_only_student_id_input_and_button(self):
        response = self.client.get("/register/check/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student ID")
        self.assertContains(response, "Check My Information")
        self.assertNotContains(response, "Bank account number")
        self.assertNotContains(response, "Full name")
        self.assertNotContains(response, "Password")

    def test_lookup_nonexistent_student_id_shows_clear_message(self):
        response = self.client.post(
            "/register/check/",
            {"student_id": "NONEXISTENT-999"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "No submission was found for Student ID “NONEXISTENT-999”.",
        )

    def test_submission_lookup_by_student_id(self):
        self.client.post("/register/", self.data)
        student = Student.objects.get(student_id="STU-001")

        response = self.client.post(
            "/register/check/",
            {"student_id": "STU-001"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "STU-001")
        self.assertContains(response, "Test Student")
        self.assertContains(response, "Computer Science")
        self.assertContains(response, "Year 1")
        self.assertContains(response, "Section A")
        self.assertContains(response, "Pending Verification")
        self.assertContains(response, "Pending Review")

        # Bank account number is displayed for verification in full with no 'Ending in' text
        self.assertContains(response, "001234")
        self.assertNotContains(response, "Ending in")

        # Bank book photo is NOT displayed
        self.assertNotContains(response, "bank_book_photos")
        self.assertNotContains(response, student.bank_book_photo.name)

        # Exact correction message
        expected_msg = (
            "Please verify that your bank account number is correct. "
            "If any information is incorrect, contact the administration "
            "to request a correction. You cannot edit your submission yourself."
        )
        self.assertContains(response, expected_msg)
