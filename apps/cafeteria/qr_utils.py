import qrcode
from io import BytesIO
from django.core.files.base import ContentFile


def generate_student_qr(student):
    """
    Generate a QR code containing the student's existing student ID.
    """
    qr = qrcode.make(student.student_id)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    filename = f"{student.student_id}_qr.png"

    return ContentFile(buffer.getvalue(), name=filename)
