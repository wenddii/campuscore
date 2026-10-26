from django.contrib import messages
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
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
    }
    return render(request, "dashboard/index.html", context)


@staff_required
def student_detail(request, student_id):
    student = get_object_or_404(
        Student.objects.select_related("department"), pk=student_id
    )
    return render(request, "dashboard/student_detail.html", {"student": student})


def _redirect_detail(student):
    return redirect("students:detail", student_id=student.pk)


@staff_required
@require_POST
def verify_student(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == "POST":
        with transaction.atomic():
            student.verification_status = Student.VerificationStatus.VERIFIED
            student.save(update_fields=["verification_status", "updated_at"])
        messages.success(request, "Student verified successfully.")
    return _redirect_detail(student)


@staff_required
@require_POST
def reject_student(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == "POST":
        student.verification_status = Student.VerificationStatus.REJECTED
        student.save(update_fields=["verification_status", "updated_at"])
        messages.success(request, "Student registration rejected.")
    return _redirect_detail(student)


@staff_required
@require_POST
def review_bank(request, student_id, decision):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == "POST":
        if decision == "approve":
            student.bank_details_status = Student.BankDetailsStatus.VERIFIED
        elif decision == "reject":
            student.bank_details_status = Student.BankDetailsStatus.REJECTED
        else:
            messages.error(request, "Invalid bank review action.")
            return _redirect_detail(student)
        student.save(update_fields=["bank_details_status", "updated_at"])
        messages.success(request, "Bank details review updated.")
    return _redirect_detail(student)
