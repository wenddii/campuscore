from django.db import models


class CafeteriaScan(models.Model):
    class MealWindow(models.TextChoices):
        WINDOW_1 = "window_1", "Window 1"
        WINDOW_2 = "window_2", "Window 2"
        WINDOW_3 = "window_3", "Window 3"
        WINDOW_4 = "window_4", "Window 4"
        WINDOW_5 = "window_5", "Window 5"
        WINDOW_6 = "window_6", "Window 6"
        WINDOW_7 = "window_7", "Window 7"
        WINDOW_8 = "window_8", "Window 8"

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,
        related_name="cafeteria_scans",
    )

    scan_date = models.DateField()
    meal_window = models.CharField(
        max_length=10,
        choices=MealWindow.choices,
    )

    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "scan_date", "meal_window"],
                name="unique_student_scan_per_window",
            )
        ]
        ordering = ["-scanned_at"]

    def __str__(self):
        return (
            f"{self.student.student_id} - "
            f"{self.scan_date} - {self.meal_window}"
        )
