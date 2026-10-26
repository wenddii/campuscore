from django import forms

from .models import Student


class OwnerStudentCreateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "student_id",
            "full_name",
            "department",
            "academic_year",
            "bank_account_number",
            "bank_book_photo",
        ]

    def clean_student_id(self):
        return self.cleaned_data["student_id"].strip()

    def clean_bank_account_number(self):
        value = self.cleaned_data.get("bank_account_number")
        return value.strip() if value else value

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("bank_book_photo"):
            self.add_error(
                "bank_book_photo",
                "Upload a bank book photo before registering the student.",
            )
        return cleaned_data


class OwnerStudentEditForm(OwnerStudentCreateForm):
    class Meta(OwnerStudentCreateForm.Meta):
        fields = [
            "full_name",
            "department",
            "academic_year",
            "bank_account_number",
            "bank_book_photo",
        ]

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("bank_book_photo") and not self.instance.bank_book_photo:
            self.add_error(
                "bank_book_photo",
                "This student must have a bank book photo.",
            )
        return cleaned_data


class VerificationStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Student.VerificationStatus.choices)


class BankDetailsStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Student.BankDetailsStatus.choices)
