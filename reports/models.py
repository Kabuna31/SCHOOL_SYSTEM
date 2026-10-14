from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from academic.models import Student
from administration.models import School, Term
from administration.managers import SchoolScopedManager


class ReportCard(models.Model):
    """Per-student, per-term report card comments and metadata."""

    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="report_cards"
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="report_cards"
    )
    term = models.ForeignKey(
        Term, on_delete=models.CASCADE, related_name="report_cards"
    )

    # Comments
    class_teacher_comment = models.CharField(
        max_length=255, blank=True,
        help_text="Short comment from the class teacher."
    )
    general_comment = models.TextField(
        blank=True,
        help_text="General comment about the student's performance."
    )
    head_teacher_comment = models.CharField(
        max_length=255, blank=True,
        help_text="Short comment from the head teacher."
    )

    # Grades
    general_grade = models.CharField(max_length=10, blank=True)

    # A Level
    points_scored = models.IntegerField(
        null=True, blank=True,
        help_text="Total points scored (A Level only).",
    )

    # Dates
    term_ended_on = models.DateField(null=True, blank=True)
    next_term_begins_on = models.DateField(null=True, blank=True)

    # Position
    position_in_class = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1)],
    )
    out_of_class = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1)],
    )

    # Attendance summary
    days_present = models.PositiveIntegerField(null=True, blank=True)
    days_absent = models.PositiveIntegerField(null=True, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SchoolScopedManager()
    unfiltered_objects = models.Manager()

    class Meta:
        unique_together = ("school", "student", "term")
        ordering = ["-term__start_date", "student__last_name", "student__first_name"]

    def __str__(self):
        return f"{self.student.full_name} - {self.term.name}"

    @classmethod
    def get_for(cls, student, term):
        """Return the report card for student+term, creating an empty one if missing."""
        school = student.school
        rc, _ = cls.unfiltered_objects.get_or_create(
            school=school,
            student=student,
            term=term,
        )
        return rc

    @property
    def attendance_summary(self):
        if self.days_present is None and self.days_absent is None:
            return ""
        return f"{self.days_present or 0} present / {self.days_absent or 0} absent"

    @property
    def position_display(self):
        if not self.position_in_class:
            return ""
        if self.out_of_class:
            return f"{self.position_in_class} / {self.out_of_class}"
        return str(self.position_in_class)