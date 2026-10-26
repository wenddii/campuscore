from django.contrib import messages
from functools import wraps
from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from .forms import (
    BankDetailsStatusForm,
    OwnerStudentCreateForm,
    OwnerStudentEditForm,
    VerificationStatusForm,
)
from .models import Student
from .models import Department


def staff_required(view):
    @login_required(login_url="login")
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            return render(request, "registration/access_denied.html", status=403)
        return view(request, *args, **kwargs)
    return wrapped


def dashboard_queryset(request):
    students = Student.objects.select_related("department").all()
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    bank_status = request.GET.get("bank_status", "")
    department_id = request.GET.get("department", "")
    if query:
        students = students.filter(
            Q(student_id__icontains=query) | Q(full_name__icontains=query)
        )
    if status in Student.VerificationStatus.values:
        students = students.filter(verification_status=status)
    if bank_status in Student.BankDetailsStatus.values:
        students = students.filter(bank_details_status=bank_status)
    if department_id.isdigit():
        students = students.filter(department_id=int(department_id))
    return students.order_by("-created_at")


@staff_required
def dashboard(request):
    selected_status = request.GET.get("status", "")
    if selected_status not in Student.VerificationStatus.values:
        selected_status = ""
    selected_bank_status = request.GET.get("bank_status", "")
    if selected_bank_status not in Student.BankDetailsStatus.values:
        selected_bank_status = ""
    selected_department_id = request.GET.get("department", "")
    selected_department = None
    if selected_department_id.isdigit():
        selected_department = Department.objects.filter(
            pk=int(selected_department_id)
        ).first()
        if selected_department is None:
            selected_department_id = ""

    all_filter_params = request.GET.copy()
    all_filter_params.pop("page", None)
    pagination_query = all_filter_params.urlencode()

    departments = Department.objects.annotate(
        total_students=Count("students"),
        pending_students=Count(
            "students",
            filter=Q(
                students__verification_status=Student.VerificationStatus.PENDING
            ),
        ),
        verified_students=Count(
            "students",
            filter=Q(
                students__verification_status=Student.VerificationStatus.VERIFIED
            ),
        ),
        rejected_students=Count(
            "students",
            filter=Q(
                students__verification_status=Student.VerificationStatus.REJECTED
            ),
        ),
        pending_bank_reviews=Count(
            "students",
            filter=Q(
                students__bank_details_status=Student.BankDetailsStatus.PENDING
            ),
        ),
    ).order_by("name")

    for department in departments:
        department_params = request.GET.copy()
        department_params.pop("page", None)
        department_params["department"] = str(department.pk)
        department.filter_url = (
            f"{reverse('students:dashboard')}?{department_params.urlencode()}"
        )

    paginator = Paginator(dashboard_queryset(request), 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {
        "students": page_obj,
        "page_obj": page_obj,
        "departments": departments,
        "selected_department": selected_department,
        "selected_department_id": selected_department_id,
        "selected_status": selected_status,
        "selected_bank_status": selected_bank_status,
        "pagination_query": pagination_query,
        "verification_choices": Student.VerificationStatus.choices,
        "bank_status_choices": Student.BankDetailsStatus.choices,
        "total_count": Student.objects.count(),
        "pending_count": Student.objects.filter(
            verification_status=Student.VerificationStatus.PENDING
        ).count(),
        "verified_count": Student.objects.filter(
            verification_status=Student.VerificationStatus.VERIFIED
        ).count(),
        "rejected_count": Student.objects.filter(
            verification_status=Student.VerificationStatus.REJECTED
        ).count(),
        "bank_review_count": Student.objects.filter(
            bank_details_status=Student.BankDetailsStatus.PENDING,
        ).count(),
        "register_url": reverse("students:register"),
    }
    return render(request, "dashboard/index.html", context)


@staff_required
def register_student(request):
    if request.method == "POST":
        form = OwnerStudentCreateForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                student = form.save(commit=False)
                student.full_clean()
                student.save()
            except IntegrityError:
                form.add_error(
                    None,
                    "A student with this student ID or bank account already exists.",
                )
            except ValidationError:
                form.add_error(
                    None,
                    "Please correct the student information before saving.",
                )
            else:
                messages.success(request, "Student registered successfully and is pending review.")
                return redirect("students:detail", student_id=student.pk)
    else:
        form = OwnerStudentCreateForm()
    return render(
        request,
        "dashboard/student_form.html",
        {
            "form": form,
            "page_title": "Register student",
            "owner_created": True,
            "cancel_url": reverse("students:dashboard"),
        },
    )


@staff_required
def student_detail(request, student_id):
    student = get_object_or_404(
        Student.objects.select_related("department"), pk=student_id
    )
    next_url = request.GET.get("next", "")
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = reverse("students:dashboard")
    return render(
        request,
        "dashboard/student_detail.html",
        {
            "student": student,
            "verification_form": VerificationStatusForm(
                initial={"status": student.verification_status}
            ),
            "bank_status_form": BankDetailsStatusForm(
                initial={"status": student.bank_details_status}
            ),
            "dashboard_url": next_url,
        },
    )


@staff_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = reverse("students:detail", args=[student.pk])
    if request.method == "POST":
        form = OwnerStudentEditForm(
            request.POST, request.FILES, instance=student
        )
        if form.is_valid():
            try:
                student = form.save(commit=False)
                student.full_clean()
                student.save()
            except IntegrityError:
                form.add_error(
                    None,
                    "A student with this bank account already exists.",
                )
            except ValidationError:
                form.add_error(
                    None,
                    "Please correct the student information before saving.",
                )
            else:
                messages.success(request, "Student information updated.")
                return redirect(next_url)
    else:
        form = OwnerStudentEditForm(instance=student)
    return render(
        request,
        "dashboard/student_form.html",
        {
            "form": form,
            "page_title": f"Edit {student.full_name}",
            "cancel_url": next_url,
            "next_url": next_url,
        },
    )


def _redirect_detail(student, next_url=""):
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(
            f"{reverse('students:detail', args=[student.pk])}?next={quote(next_url, safe='')}"
        )
    return redirect("students:detail", student_id=student.pk)


def _safe_next_url(value):
    if value.startswith("/") and not value.startswith("//"):
        return value
    return reverse("students:dashboard")


@staff_required
@require_POST
def approve_student(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    next_url = _safe_next_url(request.POST.get("next", ""))

    if (
        student.verification_status == Student.VerificationStatus.VERIFIED
        and student.bank_details_status == Student.BankDetailsStatus.VERIFIED
    ):
        messages.info(request, "This student has already been fully approved.")
        return redirect(next_url)

    student.verification_status = Student.VerificationStatus.VERIFIED
    student.bank_details_status = Student.BankDetailsStatus.VERIFIED
    try:
        student.full_clean()
    except ValidationError as error:
        errors = "; ".join(
            message
            for messages_for_field in error.message_dict.values()
            for message in messages_for_field
        )
        messages.error(
            request,
            f"Student cannot be approved. Correct the following: {errors}",
        )
        return redirect(next_url)

    with transaction.atomic():
        student.save(
            update_fields=[
                "verification_status",
                "bank_details_status",
                "updated_at",
            ]
        )
    messages.success(request, "Student registration and bank details approved.")
    return redirect(next_url)


@staff_required
@require_POST
def verify_student(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == "POST":
        student.verification_status = Student.VerificationStatus.VERIFIED
        try:
            student.full_clean()
        except ValidationError as error:
            messages.error(
                request,
                "Registration cannot be verified: "
                + "; ".join(
                    message
                    for messages_for_field in error.message_dict.values()
                    for message in messages_for_field
                ),
            )
        else:
            student.save(update_fields=["verification_status", "updated_at"])
            messages.success(request, "Student verified successfully.")
    return _redirect_detail(student, request.POST.get("next", ""))


@staff_required
@require_POST
def reject_student(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == "POST":
        student.verification_status = Student.VerificationStatus.REJECTED
        student.save(update_fields=["verification_status", "updated_at"])
        messages.success(request, "Student registration rejected.")
    return _redirect_detail(student, request.POST.get("next", ""))


@staff_required
@require_POST
def review_bank(request, student_id, decision):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == "POST":
        if decision == "approve":
            student.bank_details_status = Student.BankDetailsStatus.VERIFIED
            try:
                student.full_clean()
            except ValidationError:
                messages.error(
                    request,
                    "Bank details cannot be verified until the bank account "
                    "number and bank book photo are present.",
                )
                return _redirect_detail(student, request.POST.get("next", ""))
        elif decision == "reject":
            student.bank_details_status = Student.BankDetailsStatus.REJECTED
        else:
            messages.error(request, "Invalid bank review action.")
            return _redirect_detail(student, request.POST.get("next", ""))
        student.save(update_fields=["bank_details_status", "updated_at"])
        messages.success(request, "Bank details review updated.")
    return _redirect_detail(student, request.POST.get("next", ""))


@staff_required
@require_POST
def update_verification_status(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    form = VerificationStatusForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Select a valid registration status.")
        return _redirect_detail(student, request.POST.get("next", ""))
    status = form.cleaned_data["status"]
    if status == Student.VerificationStatus.VERIFIED:
        student.verification_status = status
        try:
            student.full_clean()
        except ValidationError:
            messages.error(
                request,
                "Registration cannot be verified until all required "
                "student and bank information is complete.",
            )
            return _redirect_detail(student, request.POST.get("next", ""))
    student.verification_status = status
    student.save(update_fields=["verification_status", "updated_at"])
    messages.success(request, "Registration status updated.")
    return _redirect_detail(student, request.POST.get("next", ""))


@staff_required
@require_POST
def update_bank_status(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    form = BankDetailsStatusForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Select a valid bank-details status.")
        return _redirect_detail(student, request.POST.get("next", ""))
    status = form.cleaned_data["status"]
    if status == Student.BankDetailsStatus.VERIFIED:
        student.bank_details_status = status
        try:
            student.full_clean()
        except ValidationError:
            messages.error(
                request,
                "Bank details cannot be verified until the account number "
                "and bank book photo are present.",
            )
            return _redirect_detail(student, request.POST.get("next", ""))
    student.bank_details_status = status
    student.save(update_fields=["bank_details_status", "updated_at"])
    messages.success(request, "Bank-details status updated.")
    return _redirect_detail(student, request.POST.get("next", ""))
