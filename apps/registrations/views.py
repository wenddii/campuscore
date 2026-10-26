
from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import render
from django.utils import timezone

from apps.students.models import Student
from .forms import StudentRegistrationForm
from .models import Registration


def register_student(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                with transaction.atomic():
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
