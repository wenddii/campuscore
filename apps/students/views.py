from django.contrib import messages
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from apps.cafeteria.qr_utils import generate_student_qr
from .models import Student


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
    student_type = request.GET.get("type", "")
    if query:
        students = students.filter(
            student_id__icontains=query
        ) | students.filter(full_name__icontains=query)
    if status in Student.VerificationStatus.values:
        students = students.filter(verification_status=status)
    if student_type in Student.StudentType.values:
        students = students.filter(student_type=student_type)
    return students.order_by("-created_at")


@staff_required
def dashboard(request):
    students = dashboard_queryset(request)
    context = {
        "students": students,
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
        "cafeteria_count": Student.objects.filter(
            student_type=Student.StudentType.CAFETERIA
        ).count(),
        "bank_review_count": Student.objects.filter(
            student_type=Student.StudentType.NON_CAFETERIA,
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
def verify_student(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == "POST":
        with transaction.atomic():
            if student.student_type != Student.StudentType.CAFETERIA:
                student.qr_code.delete(save=False)
            student.verification_status = Student.VerificationStatus.VERIFIED
            qr_exists = (
                bool(student.qr_code)
                and student.qr_code.storage.exists(student.qr_code.name)
            )
            if (
                student.student_type == Student.StudentType.CAFETERIA
                and not student.cafeteria_exempt
                and not qr_exists
            ):
                student.qr_code.save(
                    f"{student.student_id}_qr.png",
                    generate_student_qr(student),
                    save=False,
                )
            student.save()
        messages.success(request, "Student verified successfully.")
    return _redirect_detail(student)


@staff_required
def reject_student(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == "POST":
        student.verification_status = Student.VerificationStatus.REJECTED
        student.qr_code.delete(save=False)
        student.save(update_fields=["verification_status", "qr_code", "updated_at"])
        messages.success(request, "Student registration rejected.")
    return _redirect_detail(student)


@staff_required
def review_bank(request, student_id, decision):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == "POST" and student.student_type == Student.StudentType.NON_CAFETERIA:
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


@staff_required
def toggle_exempt(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == "POST":
        student.cafeteria_exempt = not student.cafeteria_exempt
        if student.cafeteria_exempt:
            student.qr_code.delete(save=False)
        elif (
            student.student_type == Student.StudentType.CAFETERIA
            and student.verification_status == Student.VerificationStatus.VERIFIED
            and (
                not student.qr_code
                or not student.qr_code.storage.exists(student.qr_code.name)
            )
        ):
            student.qr_code.save(
                f"{student.student_id}_qr.png",
                generate_student_qr(student),
                save=False,
            )
        student.save()
        messages.success(request, "Cafeteria exemption updated.")
    return _redirect_detail(student)
