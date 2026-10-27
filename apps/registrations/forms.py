
from django import forms

from apps.students.models import Student


class StudentLookupForm(forms.Form):
    student_id = forms.CharField(
        max_length=30,
        required=True,
        label="Student ID",
        widget=forms.TextInput(attrs={"placeholder": "e.g. STU-001"}),
    )

    def clean_student_id(self):
        return self.cleaned_data["student_id"].strip()


class StudentRegistrationForm(forms.ModelForm):
    bank_account_number = forms.CharField(max_length=50, required=True)
    bank_book_photo = forms.ImageField(required=True)
    confirmation_name = forms.CharField(max_length=150, required=True)
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
            "department",
            "academic_year",
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

        if not bank_account_number:
            self.add_error(
                "bank_account_number",
                "Bank account number is required.",
            )
        if not bank_book_photo:
            self.add_error(
                "bank_book_photo",
                "Upload a clear bank book photo.",
            )

        return cleaned_data
