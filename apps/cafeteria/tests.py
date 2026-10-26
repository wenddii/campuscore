from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.students.models import Department, Student


class CafeteriaWorkflowTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="Engineering", program_duration=4
        )
        self.staff = get_user_model().objects.create_user(
            username="owner", password="correct-password", is_staff=True
        )
        self.student = Student.objects.create(
            student_id="CAF-001",
            full_name="Cafeteria Student",
            department=self.department,
            academic_year="1",
            student_type=Student.StudentType.CAFETERIA,
            information_confirmed=True,
            confirmation_name="Cafeteria Student",
        )
        self.client.force_login(self.staff)

    def test_pending_student_is_rejected(self):
        response = self.client.post(
            reverse("cafeteria:scan"),
            {"student_id": self.student.student_id},
        )
        self.assertContains(response, "This registration is not verified.")

    def test_verification_generates_qr_and_scan_is_single_use(self):
        self.client.post(
            reverse("students:verify", args=[self.student.pk]),
        )
        self.student.refresh_from_db()
        self.assertTrue(self.student.qr_code)
        self.assertTrue(self.student.qr_code.storage.exists(self.student.qr_code.name))
        qr_name = self.student.qr_code.name
        self.client.post(reverse("students:verify", args=[self.student.pk]))
        self.student.refresh_from_db()
        self.assertEqual(self.student.qr_code.name, qr_name)

        first = self.client.post(
            reverse("cafeteria:scan"),
            {"student_id": self.student.student_id},
        )
        self.assertContains(first, "PASS")
        second = self.client.post(
            reverse("cafeteria:scan"),
            {"student_id": self.student.student_id},
        )
        self.assertContains(second, "already been scanned")

    def test_non_cafeteria_and_exempt_students_are_rejected(self):
        self.client.post(reverse("students:verify", args=[self.student.pk]))
        self.student.student_type = Student.StudentType.NON_CAFETERIA
        self.student.save(update_fields=["student_type"])
        response = self.client.post(
            reverse("cafeteria:scan"),
            {"student_id": self.student.student_id},
        )
        self.assertContains(response, "not registered for cafeteria access")

        self.student.student_type = Student.StudentType.CAFETERIA
        self.student.cafeteria_exempt = True
        self.student.save(update_fields=["student_type", "cafeteria_exempt"])
        response = self.client.post(
            reverse("cafeteria:scan"),
            {"student_id": self.student.student_id},
        )
        self.assertContains(response, "exempt from cafeteria access")
