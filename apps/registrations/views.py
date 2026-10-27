
from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.students.models import Student
from .forms import StudentLookupForm, StudentRegistrationForm
from .models import Registration, RegistrationSettings


def register_student(request):
    if not RegistrationSettings.get_settings().registration_open:
        return render(
            request,
            "registrations/registration_closed.html",
            status=403,
        )

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                with transaction.atomic():
                    registration_settings = RegistrationSettings.objects.select_for_update().get(
                        pk=1
                    )
                    if not registration_settings.registration_open:
                        form.add_error(
                            None,
                            "Registration is currently closed. Please contact the administration if you need assistance.",
                        )
                        return render(
                            request,
                            "registrations/register.html",
                            {"form": form},
                            status=403,
                        )
                    student = form.save(commit=False)

                    student.information_confirmed = True
                    student.confirmation_name = (
                        form.cleaned_data["confirmation_name"].strip()
                    )
                    student.confirmed_at = timezone.now()
                    student.verification_status = (
                        Student.VerificationStatus.PENDING
                    )

                    student.bank_details_status = (
                        Student.BankDetailsStatus.PENDING
                    )

                    student.full_clean()
                    student.save()

                    Registration.objects.create(
                        student=student,
                        academic_year=settings.CURRENT_ACADEMIC_YEAR,
                        status=Registration.Status.SUBMITTED,
                        student_status=Registration.StudentStatus.ACTIVE,
                        submitted_at=timezone.now(),
                    )
                    request.session["registered_student_id"] = student.student_id

                return render(
                    request,
                    "registrations/registration_success.html",
                    {"student": student},
                )

            except IntegrityError:
                form.add_error(
                    None,
                    "A student with this student ID or bank account "
                    "already exists. Please check your details.",
                )

    else:
        form = StudentRegistrationForm()

    return render(
        request,
        "registrations/register.html",
        {"form": form},
    )


def lookup_submission(request):
    student = None
    registration = None
    submission_date = None
    is_verified = False
    masked_bank_account = ""
    error_message = ""

    if request.method == "POST":
        form = StudentLookupForm(request.POST)
        if form.is_valid():
            student_id = form.cleaned_data["student_id"]
            student = (
                Student.objects.select_related("department")
                .filter(student_id__iexact=student_id)
                .first()
            )

            if student:
                registration = (
                    student.registrations.order_by("-submitted_at", "-created_at").first()
                )
                submission_date = (
                    registration.submitted_at
                    if registration and registration.submitted_at
                    else (student.confirmed_at or student.created_at)
                )
                is_verified = (
                    request.session.get("registered_student_id") == student.student_id
                )
                raw_account = student.bank_account_number or ""
                if len(raw_account) <= 4:
                    masked_bank_account = (
                        ("•" * max(0, len(raw_account) - 1)) + raw_account[-1:]
                        if raw_account
                        else ""
                    )
                else:
                    masked_bank_account = ("•" * (len(raw_account) - 4)) + raw_account[-4:]

                request.session["submitted_student_pk"] = student.pk
            else:
                error_message = f"No submission was found for Student ID “{student_id}”."
    else:
        form = StudentLookupForm()

    return render(
        request,
        "registrations/lookup.html",
        {
            "form": form,
            "student": student,
            "registration": registration,
            "submission_date": submission_date,
            "is_verified": is_verified,
            "masked_bank_account": masked_bank_account,
            "error_message": error_message,
        },
    )


def submission_status(request):
    student_pk = request.session.get("submitted_student_pk")
    if not student_pk:
        return redirect("registrations:lookup")

    student = get_object_or_404(
        Student.objects.select_related("department"), pk=student_pk
    )
    registration = (
        student.registrations.order_by("-submitted_at", "-created_at").first()
    )
    submission_date = (
        registration.submitted_at
        if registration and registration.submitted_at
        else (student.confirmed_at or student.created_at)
    )
    is_verified = (
        request.session.get("registered_student_id") == student.student_id
    )
    raw_account = student.bank_account_number or ""
    if len(raw_account) <= 4:
        masked_bank_account = (
            ("•" * max(0, len(raw_account) - 1)) + raw_account[-1:]
            if raw_account
            else ""
        )
    else:
        masked_bank_account = ("•" * (len(raw_account) - 4)) + raw_account[-4:]

    return render(
        request,
        "registrations/submission_status.html",
        {
            "student": student,
            "registration": registration,
            "submission_date": submission_date,
            "is_verified": is_verified,
            "masked_bank_account": masked_bank_account,
        },
    )
