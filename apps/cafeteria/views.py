from functools import wraps

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render
from django.utils import timezone

from apps.students.models import Student
from .models import CafeteriaScan


def staff_required(view):
    @login_required(login_url="login")
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            return render(request, "registration/access_denied.html", status=403)
        return view(request, *args, **kwargs)
    return wrapped


def current_meal_window():
    """Return the local three-hour window; midnight starts window 1.

    Eight windows therefore permit at most eight successful scans per day.
    """
    local_now = timezone.localtime()
    return local_now.date(), CafeteriaScan.MealWindow(
        f"window_{(local_now.hour // 3) + 1}"
    )


@staff_required
def scan_page(request):
    result = None
    if request.method == "POST":
        student_id = request.POST.get("student_id", "").strip()
        try:
            student = Student.objects.get(student_id=student_id)
        except Student.DoesNotExist:
            result = {"passed": False, "reason": "Student ID was not found."}
        else:
            result = {"student": student, "passed": False}
            if student.verification_status != Student.VerificationStatus.VERIFIED:
                result["reason"] = "This registration is not verified."
            elif student.student_type != Student.StudentType.CAFETERIA:
                result["reason"] = "This student is not registered for cafeteria access."
            elif student.cafeteria_exempt:
                result["reason"] = "This student is exempt from cafeteria access."
            elif not student.qr_code or not student.qr_code.storage.exists(
                student.qr_code.name
            ):
                result["reason"] = "This student does not have an eligible QR code."
            else:
                scan_date, meal_window = current_meal_window()
                try:
                    with transaction.atomic():
                        CafeteriaScan.objects.create(
                            student=student,
                            scan_date=scan_date,
                            meal_window=meal_window,
                        )
                except IntegrityError:
                    result["reason"] = "This student has already been scanned in the current three-hour window."
                else:
                    result["passed"] = True
                    result["reason"] = "Access granted for the current three-hour window."
    return render(request, "cafeteria/scan.html", {"result": result})

# Create your views here.
