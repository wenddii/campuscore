
from django import forms

from apps.students.models import Student


class StudentRegistrationForm(forms.ModelForm):
    photo = forms.ImageField(required=False)
    bank_book_photo = forms.ImageField(required=False)
    information_confirmed = forms.BooleanField(
        required=True,
        label=(
            "I confirm that the information I submitted "
            "is accurate and complete."
        ),
    )

    class Meta:
        model = Student
        fields = [
            "student_id",
            "full_name",
            "photo",
            "department",
            "academic_year",
            "student_type",
            "bank_account_number",
            "bank_book_photo",
            "confirmation_name",
            "information_confirmed",
        ]

    def clean_student_id(self):
        return self.cleaned_data["student_id"].strip()

    def clean_bank_account_number(self):
        account_number = self.cleaned_data.get(
            "bank_account_number"
        )

        if not account_number or not account_number.strip():
            return None

        return account_number.strip()

    def clean(self):
        cleaned_data = super().clean()

        student_type = cleaned_data.get("student_type")
        photo = cleaned_data.get("photo")
        bank_account_number = cleaned_data.get("bank_account_number")
        bank_book_photo = cleaned_data.get("bank_book_photo")
        confirmation_name = cleaned_data.get("confirmation_name")
        full_name = cleaned_data.get("full_name")
        confirmed = cleaned_data.get("information_confirmed")

        if confirmed and confirmation_name and full_name:
            if confirmation_name.strip().casefold() != full_name.strip().casefold():
                self.add_error(
                    "confirmation_name",
                    "Enter your full name as written above to confirm.",
                )

        if student_type == Student.StudentType.CAFETERIA:
            if not photo:
                self.add_error(
                    "photo",
                    "A student photo is required for cafeteria registration.",
                )
            if bank_account_number or bank_book_photo:
                self.add_error(
                    "student_type",
                    "Cafeteria students must not submit bank details.",
                )
            cleaned_data["bank_account_number"] = None
            cleaned_data["bank_book_photo"] = None
        elif student_type == Student.StudentType.NON_CAFETERIA:
            if photo:
                self.add_error(
                    "student_type",
                    "Non-cafeteria students must not submit a student photo.",
                )
            if not bank_account_number:
                self.add_error(
                    "bank_account_number",
                    "Bank account number is required for non-cafeteria registration.",
                )
            if not bank_book_photo:
                self.add_error(
                    "bank_book_photo",
                    "Upload a clear bank book photo for non-cafeteria registration.",
                )
            cleaned_data["photo"] = None

        return cleaned_data
