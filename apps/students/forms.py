from django import forms

from .models import Section, Student


class OwnerStudentCreateForm(forms.ModelForm):
    section = forms.ModelChoiceField(
        queryset=Section.objects.select_related("department").all(),
        required=False,
        empty_label="Select section",
    )

    class Meta:
        model = Student
        fields = [
            "student_id",
            "full_name",
            "department",
            "academic_year",
            "section",
            "bank_account_number",
            "bank_book_photo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        department_id = None
        if self.is_bound:
            department_id = self.data.get("department")
        elif self.instance and self.instance.pk and self.instance.department_id:
            department_id = self.instance.department_id

        if department_id and str(department_id).isdigit():
            self.fields["section"].queryset = Section.objects.filter(
                department_id=int(department_id)
            )
        else:
            self.fields["section"].queryset = Section.objects.select_related("department").all()

    def clean_student_id(self):
        return self.cleaned_data["student_id"].strip()

    def clean_bank_account_number(self):
        value = self.cleaned_data.get("bank_account_number")
        return value.strip() if value else value

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get("department")
        section = cleaned_data.get("section")
        if department:
            if department.sections.exists():
                if not section:
                    self.add_error(
                        "section",
                        f"Please select a section for {department.name}.",
                    )
                elif section.department_id != department.id:
                    self.add_error(
                        "section",
                        f"The selected section does not belong to {department.name}.",
                    )
            else:
                if section:
                    self.add_error(
                        "section",
                        f"{department.name} does not have sections. Leave this field empty.",
                    )
                    cleaned_data["section"] = None

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
            "section",
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
