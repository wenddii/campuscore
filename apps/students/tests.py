from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .models import Department, Student


def image_upload(name="bank-book.png"):
    image = Image.new("RGB", (10, 10), "white")
    stream = BytesIO()
    image.save(stream, format="PNG")
    return SimpleUploadedFile(name, stream.getvalue(), content_type="image/png")


class DashboardFilteringTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="dashboard-owner",
            password="correct-password",
            is_staff=True,
        )
        self.department = Department.objects.create(
            name="Computer Science",
            program_duration=4,
        )
        self.other_department = Department.objects.create(
            name="Business",
            program_duration=4,
        )
        self.student = Student.objects.create(
            student_id="CS-001",
            full_name="Computer Student",
            department=self.department,
            academic_year="1",
            bank_account_number="100001",
            verification_status=Student.VerificationStatus.PENDING,
            bank_details_status=Student.BankDetailsStatus.PENDING,
        )
        Student.objects.create(
            student_id="BUS-001",
            full_name="Business Student",
            department=self.other_department,
            academic_year="1",
            bank_account_number="100002",
            verification_status=Student.VerificationStatus.VERIFIED,
            bank_details_status=Student.BankDetailsStatus.VERIFIED,
        )
        self.client.force_login(self.owner)

    def test_department_and_status_filters_combine(self):
        response = self.client.get(
            reverse("students:dashboard"),
            {
                "department": self.department.pk,
                "status": Student.VerificationStatus.PENDING,
                "bank_status": Student.BankDetailsStatus.PENDING,
                "q": "Computer",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CS-001")
        self.assertNotContains(response, "BUS-001")
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_all_departments_and_overview_counts(self):
        response = self.client.get(reverse("students:dashboard"))
        self.assertContains(response, "CS-001")
        self.assertContains(response, "BUS-001")
        overview = next(
            department
            for department in response.context["departments"]
            if department.pk == self.department.pk
        )
        self.assertEqual(overview.total_students, 1)
        self.assertEqual(overview.pending_students, 1)
        self.assertEqual(overview.pending_bank_reviews, 1)


class StudentManagementTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="management-owner",
            password="correct-password",
            is_staff=True,
        )
        self.department = Department.objects.create(
            name="Engineering",
            program_duration=4,
        )
        self.client.force_login(self.owner)

    def student_data(self, **overrides):
        data = {
            "student_id": "ENG-001",
            "full_name": "Managed Student",
            "department": self.department.pk,
            "academic_year": "1",
            "bank_account_number": "900001",
        }
        data.update(overrides)
        return data

    def test_owner_can_register_student_without_false_declaration(self):
        data = self.student_data()
        data["bank_book_photo"] = image_upload()
        response = self.client.post(
            reverse("students:register"),
            data,
        )
        student = Student.objects.get(student_id="ENG-001")
        self.assertRedirects(response, reverse("students:detail", args=[student.pk]))
        self.assertFalse(student.information_confirmed)
        self.assertEqual(student.verification_status, Student.VerificationStatus.PENDING)

    def test_duplicate_student_id_is_rejected(self):
        Student.objects.create(
            **self.student_data(department=self.department),
            bank_book_photo=image_upload("existing.png"),
        )
        data = self.student_data(bank_account_number="900002")
        data["bank_book_photo"] = image_upload("duplicate.png")
        response = self.client.post(
            reverse("students:register"),
            data,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertEqual(Student.objects.filter(student_id="ENG-001").count(), 1)

    def test_duplicate_bank_account_is_rejected(self):
        Student.objects.create(
            **self.student_data(department=self.department),
            bank_book_photo=image_upload("existing-account.png"),
        )
        data = self.student_data(student_id="ENG-002")
        data["bank_book_photo"] = image_upload("duplicate-account.png")
        response = self.client.post(reverse("students:register"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertEqual(Student.objects.count(), 1)

    def test_owner_can_edit_and_replace_bank_book_photo(self):
        student = Student.objects.create(
            **self.student_data(department=self.department),
            bank_book_photo=image_upload("old.png"),
        )
        old_name = student.bank_book_photo.name
        response = self.client.post(
            reverse("students:edit", args=[student.pk]),
            {
                **self.student_data(
                    department=self.department.pk,
                    full_name="Corrected Student",
                    bank_account_number="900003",
                ),
                "bank_book_photo": image_upload("new.png"),
            },
        )
        self.assertRedirects(response, reverse("students:detail", args=[student.pk]))
        student.refresh_from_db()
        self.assertEqual(student.full_name, "Corrected Student")
        self.assertEqual(student.bank_account_number, "900003")
        self.assertNotEqual(student.bank_book_photo.name, old_name)

    def test_statuses_are_independent_and_verification_is_validated(self):
        student = Student.objects.create(
            **self.student_data(department=self.department),
            bank_book_photo=image_upload("complete.png"),
        )
        self.client.post(
            reverse("students:update_status", args=[student.pk]),
            {"status": Student.VerificationStatus.VERIFIED},
        )
        student.refresh_from_db()
        self.assertEqual(student.verification_status, Student.VerificationStatus.VERIFIED)
        self.assertEqual(student.bank_details_status, Student.BankDetailsStatus.PENDING)

        incomplete = Student.objects.create(
            student_id="ENG-002",
            full_name="Incomplete Student",
            department=self.department,
            academic_year="1",
            bank_account_number="900004",
        )
        response = self.client.post(
            reverse("students:update_bank_status", args=[incomplete.pk]),
            {"status": Student.BankDetailsStatus.VERIFIED},
            follow=True,
        )
        self.assertRedirects(response, reverse("students:detail", args=[incomplete.pk]))
        incomplete.refresh_from_db()
        self.assertEqual(incomplete.bank_details_status, Student.BankDetailsStatus.PENDING)
        self.assertContains(response, "cannot be verified")

    def test_one_click_approval_updates_both_statuses_and_preserves_filters(self):
        student = Student.objects.create(
            **self.student_data(department=self.department),
            bank_book_photo=image_upload("approve.png"),
        )
        dashboard_url = (
            f"{reverse('students:dashboard')}?"
            f"department={self.department.pk}&status=pending"
        )
        response = self.client.post(
            reverse("students:approve", args=[student.pk]),
            {"next": dashboard_url},
        )
        self.assertRedirects(response, dashboard_url)
        student.refresh_from_db()
        self.assertEqual(
            student.verification_status,
            Student.VerificationStatus.VERIFIED,
        )
        self.assertEqual(
            student.bank_details_status,
            Student.BankDetailsStatus.VERIFIED,
        )

        list_response = self.client.get(reverse("students:dashboard"))
        self.assertContains(list_response, "Approved")
        self.assertNotContains(
            list_response,
            f'action="{reverse("students:approve", args=[student.pk])}"',
        )

    def test_incomplete_student_cannot_be_approved(self):
        student = Student.objects.create(
            student_id="ENG-003",
            full_name="Incomplete Student",
            department=self.department,
            academic_year="1",
            bank_account_number="900005",
        )
        response = self.client.post(
            reverse("students:approve", args=[student.pk]),
            {"next": reverse("students:dashboard")},
            follow=True,
        )
        student.refresh_from_db()
        self.assertEqual(student.verification_status, Student.VerificationStatus.PENDING)
        self.assertEqual(student.bank_details_status, Student.BankDetailsStatus.PENDING)
        self.assertContains(response, "Bank book photo is required")

    def test_unauthorized_user_cannot_approve_student(self):
        student = Student.objects.create(
            **self.student_data(department=self.department),
            bank_book_photo=image_upload("unauthorized.png"),
        )
        self.client.logout()
        response = self.client.post(
            reverse("students:approve", args=[student.pk]),
            {"next": reverse("students:dashboard")},
        )
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('students:approve', args=[student.pk])}",
        )
        student.refresh_from_db()
        self.assertEqual(student.verification_status, Student.VerificationStatus.PENDING)

    def test_unauthorized_users_cannot_manage_students(self):
        self.client.logout()
        self.assertRedirects(
            self.client.get(reverse("students:register")),
            f"{reverse('login')}?next={reverse('students:register')}",
        )
        self.assertRedirects(
            self.client.post(
                reverse("students:update_status", args=[1]),
                {"status": Student.VerificationStatus.REJECTED},
            ),
            f"{reverse('login')}?next={reverse('students:update_status', args=[1])}",
        )

# Create your tests here.
