from io import BytesIO
import csv

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .models import Department, Section, Student
from apps.registrations.models import RegistrationSettings


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

    def test_academic_year_and_department_filters_alone_and_combined(self):
        Student.objects.create(
            student_id="CS-002",
            full_name="Computer Year 2",
            department=self.department,
            academic_year="2",
            bank_account_number="100003",
        )
        Student.objects.create(
            student_id="BUS-002",
            full_name="Business Year 2",
            department=self.other_department,
            academic_year="2",
            bank_account_number="100004",
        )

        # Academic year alone: Year 2
        response_year = self.client.get(
            reverse("students:dashboard"),
            {"academic_year": "2"},
        )
        self.assertContains(response_year, "CS-002")
        self.assertContains(response_year, "BUS-002")
        self.assertNotContains(response_year, "CS-001")
        self.assertEqual(response_year.context["page_obj"].paginator.count, 2)

        # Department alone: Computer Science
        response_dept = self.client.get(
            reverse("students:dashboard"),
            {"department": self.department.pk},
        )
        self.assertContains(response_dept, "CS-001")
        self.assertContains(response_dept, "CS-002")
        self.assertNotContains(response_dept, "BUS-001")
        self.assertNotContains(response_dept, "BUS-002")
        self.assertEqual(response_dept.context["page_obj"].paginator.count, 2)

        # Combined: Computer Science + Year 2
        response_combined = self.client.get(
            reverse("students:dashboard"),
            {
                "department": self.department.pk,
                "academic_year": "2",
            },
        )
        self.assertContains(response_combined, "CS-002")
        self.assertNotContains(response_combined, "CS-001")
        self.assertNotContains(response_combined, "BUS-001")
        self.assertNotContains(response_combined, "BUS-002")
        self.assertEqual(response_combined.context["page_obj"].paginator.count, 1)

        # Preserved in pagination and export query
        self.assertIn("academic_year=2", response_combined.context["pagination_query"])
        self.assertIn(f"department={self.department.pk}", response_combined.context["pagination_query"])
        self.assertEqual(
            response_combined.context["pagination_query"],
            response_combined.context["export_query"],
        )

    def test_section_filter_alone_and_combined(self):
        cs_sec_a = Section.objects.create(department=self.department, name="Section A")
        cs_sec_b = Section.objects.create(department=self.department, name="Section B")
        bus_sec_a = Section.objects.create(department=self.other_department, name="Section A")

        Student.objects.create(
            student_id="CS-Y2-A",
            full_name="CS Year 2 Section A",
            department=self.department,
            academic_year="2",
            section=cs_sec_a,
            bank_account_number="100010",
        )
        Student.objects.create(
            student_id="CS-Y2-B",
            full_name="CS Year 2 Section B",
            department=self.department,
            academic_year="2",
            section=cs_sec_b,
            bank_account_number="100011",
        )
        Student.objects.create(
            student_id="BUS-Y2-A",
            full_name="BUS Year 2 Section A",
            department=self.other_department,
            academic_year="2",
            section=bus_sec_a,
            bank_account_number="100012",
        )

        # Section alone: Section B
        response_sec = self.client.get(
            reverse("students:dashboard"),
            {"section": cs_sec_b.pk},
        )
        self.assertContains(response_sec, "CS-Y2-B")
        self.assertNotContains(response_sec, "CS-Y2-A")
        self.assertNotContains(response_sec, "BUS-Y2-A")
        self.assertEqual(response_sec.context["page_obj"].paginator.count, 1)

        # Combined: Computer Science + Year 2 + Section A
        response_all = self.client.get(
            reverse("students:dashboard"),
            {
                "department": self.department.pk,
                "academic_year": "2",
                "section": cs_sec_a.pk,
            },
        )
        self.assertContains(response_all, "CS-Y2-A")
        self.assertNotContains(response_all, "CS-Y2-B")
        self.assertNotContains(response_all, "BUS-Y2-A")
        self.assertNotContains(response_all, "CS-001")
        self.assertEqual(response_all.context["page_obj"].paginator.count, 1)

        # Preserved in pagination and export query
        self.assertIn(f"section={cs_sec_a.pk}", response_all.context["pagination_query"])
        self.assertIn("academic_year=2", response_all.context["pagination_query"])
        self.assertIn(f"department={self.department.pk}", response_all.context["pagination_query"])
        self.assertEqual(
            response_all.context["pagination_query"],
            response_all.context["export_query"],
        )

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

    def test_staff_can_close_and_reopen_registration(self):
        response = self.client.post(reverse("students:toggle_registration"))
        self.assertRedirects(response, reverse("students:dashboard"))
        self.assertFalse(RegistrationSettings.get_settings().registration_open)

        response = self.client.post(reverse("students:toggle_registration"))
        self.assertRedirects(response, reverse("students:dashboard"))
        self.assertTrue(RegistrationSettings.get_settings().registration_open)

    def test_students_cannot_change_registration_state(self):
        self.client.logout()
        response = self.client.post(reverse("students:toggle_registration"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('students:toggle_registration')}",
        )

    def test_authenticated_student_cannot_access_dashboard_or_controls(self):
        student_user = get_user_model().objects.create_user(
            username="student-user",
            password="student-password",
            is_staff=False,
        )
        self.client.force_login(student_user)

        dashboard_response = self.client.get(reverse("students:dashboard"))
        toggle_response = self.client.post(reverse("students:toggle_registration"))

        self.assertEqual(dashboard_response.status_code, 403)
        self.assertEqual(toggle_response.status_code, 403)


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

    def test_owner_can_edit_student_section(self):
        sec_a = Section.objects.create(department=self.department, name="Section A")
        sec_b = Section.objects.create(department=self.department, name="Section B")
        student = Student.objects.create(
            **self.student_data(
                department=self.department,
                section=sec_a,
            ),
            bank_book_photo=image_upload("sec.png"),
        )
        response = self.client.post(
            reverse("students:edit", args=[student.pk]),
            {
                **self.student_data(
                    department=self.department.pk,
                    section=sec_b.pk,
                ),
            },
        )
        self.assertRedirects(response, reverse("students:detail", args=[student.pk]))
        student.refresh_from_db()
        self.assertEqual(student.section, sec_b)


class StudentCsvExportTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="csv-owner",
            password="correct-password",
            is_staff=True,
        )
        self.department = Department.objects.create(
            name="Data Science",
            program_duration=4,
        )
        self.other_department = Department.objects.create(
            name="Law",
            program_duration=4,
        )
        self.client.force_login(self.owner)

    def create_student(self, student_id, department, name, account):
        return Student.objects.create(
            student_id=student_id,
            full_name=name,
            department=department,
            academic_year="1",
            bank_account_number=account,
        )

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

    def test_csv_export_has_exact_columns_and_all_matching_records(self):
        self.create_student("DS-001", self.department, "Amina", "100001")
        self.create_student("DS-002", self.department, "Bekele", "100002")
        self.create_student("LAW-001", self.other_department, "Chala", "100003")

        response = self.client.get(
            reverse("students:export_csv"),
            {
                "department": self.department.pk,
                "status": Student.VerificationStatus.PENDING,
                "q": "DS",
                "page": 2,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment;", response["Content-Disposition"])
        rows = list(csv.reader(response.content.decode("utf-8").splitlines()))
        self.assertEqual(
            rows[0],
            ["Student Name", "Department", "Bank Account Number"],
        )
        self.assertEqual(len(rows), 3)
        self.assertEqual({row[0] for row in rows[1:]}, {"Amina", "Bekele"})
        self.assertNotIn("Chala", response.content.decode("utf-8"))
        self.assertNotIn("<html", response.content.decode("utf-8"))

    def test_csv_export_filters_by_academic_year_and_department(self):
        Student.objects.create(
            student_id="DS-Y1",
            full_name="DS Year 1",
            department=self.department,
            academic_year="1",
            bank_account_number="200001",
        )
        Student.objects.create(
            student_id="DS-Y2",
            full_name="DS Year 2",
            department=self.department,
            academic_year="2",
            bank_account_number="200002",
        )
        Student.objects.create(
            student_id="LAW-Y2",
            full_name="Law Year 2",
            department=self.other_department,
            academic_year="2",
            bank_account_number="200003",
        )

        # Export with both department and academic_year
        response = self.client.get(
            reverse("students:export_csv"),
            {
                "department": self.department.pk,
                "academic_year": "2",
            },
        )
        self.assertEqual(response.status_code, 200)
        rows = list(csv.reader(response.content.decode("utf-8").splitlines()))
        self.assertEqual(len(rows), 2)  # header + 1 student
        self.assertEqual(rows[1][0], "DS Year 2")
        self.assertEqual(rows[1][1], self.department.name)

    def test_csv_export_filters_by_section_and_combined_filters(self):
        sec_ds_a = Section.objects.create(department=self.department, name="A")
        sec_ds_b = Section.objects.create(department=self.department, name="B")
        sec_law_a = Section.objects.create(department=self.other_department, name="A")

        Student.objects.create(
            student_id="DS-Y2-A",
            full_name="DS Year 2 Sec A",
            department=self.department,
            academic_year="2",
            section=sec_ds_a,
            bank_account_number="200010",
        )
        Student.objects.create(
            student_id="DS-Y2-B",
            full_name="DS Year 2 Sec B",
            department=self.department,
            academic_year="2",
            section=sec_ds_b,
            bank_account_number="200011",
        )
        Student.objects.create(
            student_id="LAW-Y2-A",
            full_name="Law Year 2 Sec A",
            department=self.other_department,
            academic_year="2",
            section=sec_law_a,
            bank_account_number="200012",
        )

        # Export combined: Data Science + Year 2 + Section A
        response = self.client.get(
            reverse("students:export_csv"),
            {
                "department": self.department.pk,
                "academic_year": "2",
                "section": sec_ds_a.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        rows = list(csv.reader(response.content.decode("utf-8").splitlines()))
        self.assertEqual(rows[0], ["Student Name", "Department", "Bank Account Number"])
        self.assertEqual(len(rows), 2)  # header + 1 record
        self.assertEqual(rows[1][0], "DS Year 2 Sec A")
        self.assertEqual(rows[1][1], self.department.name)
        self.assertEqual(rows[1][2], "200010")

        # Export section alone: Section B
        response_b = self.client.get(
            reverse("students:export_csv"),
            {"section": sec_ds_b.pk},
        )
        rows_b = list(csv.reader(response_b.content.decode("utf-8").splitlines()))
        self.assertEqual(rows_b[0], ["Student Name", "Department", "Bank Account Number"])
        self.assertEqual(len(rows_b), 2)
        self.assertEqual(rows_b[1][0], "DS Year 2 Sec B")

    def test_csv_export_neutralizes_formula_values(self):
        self.create_student(
            "DS-003",
            self.department,
            "=Injected",
            "+100004",
        )
        response = self.client.get(reverse("students:export_csv"))
        rows = list(csv.reader(response.content.decode("utf-8").splitlines()))
        self.assertEqual(rows[1][0], "'=Injected")
        self.assertEqual(rows[1][2], "'+100004")

    def test_unauthorized_users_cannot_export_csv(self):
        self.client.logout()
        response = self.client.get(reverse("students:export_csv"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('students:export_csv')}",
        )

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


class DepartmentSectionModelTests(TestCase):
    def test_department_can_be_created_without_sections(self):
        dept = Department.objects.create(name="Information Systems", program_duration=4)
        self.assertEqual(dept.sections.count(), 0)

    def test_department_can_have_multiple_sections(self):
        dept = Department.objects.create(name="Computer Science", program_duration=4)
        sec1 = Section.objects.create(department=dept, name="Section 1")
        sec2 = Section.objects.create(department=dept, name="Section 2")
        self.assertEqual(list(dept.sections.values_list("name", flat=True)), ["Section 1", "Section 2"])

    def test_duplicate_section_name_within_same_department_rejected(self):
        dept = Department.objects.create(name="Business", program_duration=4)
        Section.objects.create(department=dept, name="Section A")
        with self.assertRaises(IntegrityError):
            Section.objects.create(department=dept, name="Section A")

    def test_same_section_name_in_different_departments_allowed(self):
        dept1 = Department.objects.create(name="Accounting", program_duration=4)
        dept2 = Department.objects.create(name="Marketing", program_duration=4)
        sec1 = Section.objects.create(department=dept1, name="Section A")
        sec2 = Section.objects.create(department=dept2, name="Section A")
        self.assertIsNotNone(sec1.pk)
        self.assertIsNotNone(sec2.pk)
        self.assertNotEqual(sec1.pk, sec2.pk)

    def test_student_clean_requires_section_if_department_has_sections(self):
        dept = Department.objects.create(name="Physics", program_duration=4)
        Section.objects.create(department=dept, name="Lab 1")
        student = Student(
            student_id="PHY-001",
            full_name="Physics Student",
            department=dept,
            academic_year="1",
            bank_account_number="112233",
            section=None,
        )
        with self.assertRaises(ValidationError) as ctx:
            student.clean()
        self.assertIn("section", ctx.exception.message_dict)

    def test_student_clean_allows_null_section_if_department_has_no_sections(self):
        dept = Department.objects.create(name="Philosophy", program_duration=4)
        student = Student(
            student_id="PHIL-001",
            full_name="Philosophy Student",
            department=dept,
            academic_year="1",
            bank_account_number="112234",
            section=None,
        )
        # Should not raise
        student.clean()

    def test_student_clean_rejects_section_belonging_to_another_department(self):
        dept1 = Department.objects.create(name="Chemistry", program_duration=4)
        dept2 = Department.objects.create(name="Biology", program_duration=4)
        sec_bio = Section.objects.create(department=dept2, name="Bio Sec 1")
        student = Student(
            student_id="CHEM-001",
            full_name="Chem Student",
            department=dept1,
            academic_year="1",
            bank_account_number="112235",
            section=sec_bio,
        )
        with self.assertRaises(ValidationError) as ctx:
            student.clean()
        self.assertIn("section", ctx.exception.message_dict)
