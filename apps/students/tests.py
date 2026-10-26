from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Department, Student


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

# Create your tests here.
