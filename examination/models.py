import logging
import datetime
from django.conf import settings
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from academic.models import Student, Teacher, ClassRoom, StudentClassEnrollment, Subject
from administration.models import AcademicYear, Term, School
from administration.managers import SchoolScopedManager


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ugandan grading constants
# ---------------------------------------------------------------------------
# O-Level (UCE): New competence-based curriculum (A-E).
#   CA (20%) + EoC (80%). No divisions. D is the minimum pass for a certificate.
#
# A-Level (UACE): Proposed reform (expected ~2028).
#   Grades A-E (no O/F). Points: A=5, B=4, C=3, D=2, E=1.
#   Max total score (incl. subsidiaries) expected to be 20.
#   CA (20%) + National Exam (80%). Final details still being piloted.


class GradeScale(models.Model):
    """Translate a numeric score to a Ugandan grade scale.

    Supports the new O-Level (UCE) and proposed A-Level (UACE) scales.
    """

    class Level(models.TextChoices):
        O_LEVEL = "O", "O-Level (UCE, New Curriculum)"
        A_LEVEL = "A", "A-Level (UACE, Proposed 2028)"

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="grade_scales")
    name = models.CharField(max_length=255)
    level = models.CharField(
        max_length=1,
        choices=Level.choices,
        default=Level.O_LEVEL,
        help_text="O-Level uses A-E; A-Level uses the proposed A-E scale.",
    )

    objects = SchoolScopedManager()
    unfiltered_objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "name"],
                name="unique_school_grade_scale",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"

    def get_rule(self, grade):
        if grade is None:
            return None
        rule = self.gradescalerule_set.filter(
            min_grade__lte=grade, max_grade__gte=grade
        ).first()
        if not rule:
            logger.debug("No grade scale rule matched numeric grade %s.", grade)
        return rule

    def to_letter(self, grade):
        rule = self.get_rule(grade)
        return rule.letter_grade if rule else None

    def to_numeric(self, grade):
        rule = self.get_rule(grade)
        return rule.numeric_scale if rule else None

    @classmethod
    def seed_new_lower_secondary_scale(cls, school, name="New Lower Secondary (UCE)"):
        """Create the A-E competence-based scale for Uganda's new O-Level curriculum."""
        scale, _ = cls.objects.get_or_create(
            school=school, name=name,
            defaults={"level": cls.Level.O_LEVEL},
        )
        rules = [
            (80.00, 100.00, "A", 5),
            (70.00,  79.99, "B", 4),
            (60.00,  69.99, "C", 3),
            (50.00,  59.99, "D", 2),
            ( 0.00,  49.99, "E", 1),
        ]
        for mn, mx, letter, pts in rules:
            GradeScaleRule.unfiltered_objects.get_or_create(
                school=school, grade_scale=scale,
                min_grade=mn, max_grade=mx,
                defaults={"letter_grade": letter, "numeric_scale": pts},
            )
        return scale

    @classmethod
    def seed_proposed_uace_scale(cls, school, name="Proposed UACE (2028)"):
        """Create the proposed A-E scale for A-Level (UACE)."""
        scale, _ = cls.objects.get_or_create(
            school=school, name=name,
            defaults={"level": cls.Level.A_LEVEL},
        )
        rules = [
            (80.00, 100.00, "A", 5),
            (70.00,  79.99, "B", 4),
            (60.00,  69.99, "C", 3),
            (50.00,  59.99, "D", 2),
            ( 0.00,  49.99, "E", 1),
        ]
        for mn, mx, letter, pts in rules:
            GradeScaleRule.unfiltered_objects.get_or_create(
                school=school, grade_scale=scale,
                min_grade=mn, max_grade=mx,
                defaults={"letter_grade": letter, "numeric_scale": pts},
            )
        return scale


class GradeScaleRule(models.Model):
    """One rule for a grade scale (a score band → Ugandan letter + points)."""

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="grade_scale_rules")
    min_grade = models.DecimalField(max_digits=5, decimal_places=2)
    max_grade = models.DecimalField(max_digits=5, decimal_places=2)
    letter_grade = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="O-Level: A-E. A-Level: A-E (proposed).",
    )
    numeric_scale = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        help_text="Points value. O-Level: 5 (A) - 1 (E). A-Level: 5 (A) - 1 (E).",
    )
    grade_scale = models.ForeignKey(GradeScale, on_delete=models.CASCADE)

    objects = SchoolScopedManager()
    unfiltered_objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "grade_scale", "min_grade", "max_grade"],
                name="unique_school_grade_scale_rule",
            )
        ]
        indexes = [
            models.Index(fields=["min_grade", "max_grade", "grade_scale"]),
        ]

    def __str__(self):
        return f"{self.min_grade}-{self.max_grade} {self.letter_grade} ({self.numeric_scale} pts)"

    def clean(self):
        if not self.letter_grade and self.numeric_scale is None:
            raise ValidationError(
                "Either a letter grade or numeric points value must be provided."
            )
        if self.letter_grade and self.numeric_scale is None:
            raise ValidationError(
                "If a letter grade is provided, the points value must also be provided."
            )
        if self.numeric_scale is not None and not self.letter_grade:
            raise ValidationError(
                "If a points value is provided, a letter grade must also be provided."
            )
        if self.grade_scale_id:
            if not (1 <= float(self.numeric_scale) <= 5):
                raise ValidationError(
                    {"numeric_scale": "Points must be between 1 and 5."}
                )

    def save(self, *args, **kwargs):
        if self.min_grade >= self.max_grade:
            raise ValidationError("min_grade must be less than max_grade.")
        self.clean()
        super().save(*args, **kwargs)


class Result(models.Model):
    """Per-subject result combining CA (20%) and final exam (80%).

    This is the canonical results model — one row per (student, subject,
    academic_year, term). Replaces both the old per-term `Result` and the
    intermediate `SubjectResult`.
    """

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, blank=True, null=True)

    ca_score = models.FloatField(null=True, blank=True)
    exam_score = models.FloatField(null=True, blank=True)
    final_score = models.FloatField(null=True, blank=True)

    letter_grade = models.CharField(max_length=5, blank=True, null=True)
    points = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    grade_scale = models.ForeignKey(
        GradeScale, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Scale used to map final_score to letter_grade and points.",
    )

    objects = SchoolScopedManager()
    unfiltered_objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "student", "subject", "academic_year", "term"],
                name="unique_school_student_term_result",
            )
        ]
        ordering = ("student__admission_number", "subject__name")

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.final_score}"

    def compute_final(self, ca_weight=0.20, exam_weight=0.80):
        if self.ca_score is None and self.exam_score is None:
            self.final_score = None
            return
        ca = self.ca_score or 0.0
        ex = self.exam_score or 0.0
        self.final_score = round(ca * ca_weight + ex * exam_weight, 2)

    def apply_grade_scale(self):
        if self.final_score is None or not self.grade_scale_id:
            return
        rule = self.grade_scale.get_rule(self.final_score)
        if rule:
            self.letter_grade = rule.letter_grade
            self.points = rule.numeric_scale

    def save(self, *args, **kwargs):
        self.compute_final()
        self.apply_grade_scale()
        super().save(*args, **kwargs)


class ExaminationListHandler(models.Model):
    """A scheduled exam / assessment event in a Ugandan secondary school."""

    ASSESSMENT_TYPE_CHOICES = (
        ("BOT", "Beginning of Term (BOT)"),
        ("MOT", "Mid of Term (MOT)"),
        ("EOT", "End of Term (EOT)"),
        ("CA",  "Continuous Assessment (CA)"),
        ("MOCK", "Mock Examination"),
        ("UCE", "UCE (National O-Level)"),
        ("UACE", "UACE (National A-Level)"),
    )

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="examinations")
    name = models.CharField(max_length=100)
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="examinations",
        null=True,
        blank=True,
    )
    assessment_type = models.CharField(
        max_length=4,
        choices=ASSESSMENT_TYPE_CHOICES,
        default="EOT",
    )
    start_date = models.DateField()
    ends_date = models.DateField()
    out_of = models.IntegerField(
        default=100,
        help_text="Maximum marks. Ugandan school assessments are normally out of 100.",
    )
    classrooms = models.ManyToManyField(ClassRoom, related_name="class_exams")
    comments = models.CharField(
        max_length=200, blank=True, null=True, help_text="Comments regarding the exam."
    )
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    objects = SchoolScopedManager()
    unfiltered_objects = models.Manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["school", "name"], name="unique_school_exam_name")
        ]

    @property
    def status(self):
        today = datetime.date.today()
        if today > self.ends_date:
            return "Done"
        elif self.start_date <= today <= self.ends_date:
            return "Ongoing"
        return "Coming Up"

    def __str__(self):
        return self.name

    def clean(self):
        if self.start_date > self.ends_date:
            raise ValidationError("Start date cannot be later than end date.")
        if (
            self.term_id
            and self.term.academic_year.school_id
            and self.term.academic_year.school_id != self.school_id
        ):
            raise ValidationError("The selected term belongs to another school.")
        super().clean()


class MarksManagement(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="marks_management")
    exam_name = models.ForeignKey(
        ExaminationListHandler, on_delete=models.CASCADE, related_name="exam_marks"
    )
    points_scored = models.FloatField()
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="subject_marks"
    )
    student = models.ForeignKey(
        StudentClassEnrollment, on_delete=models.CASCADE, related_name="student_marks"
    )
    created_by = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name="marks_entered"
    )
    date_time = models.DateTimeField(auto_now_add=True)

    objects = SchoolScopedManager()
    unfiltered_objects = models.Manager()

    def __str__(self):
        return f"{self.exam_name} - {self.student} - {self.points_scored}"

    def clean(self):
        if self.points_scored < 0 or self.points_scored > self.exam_name.out_of:
            raise ValidationError(
                f"Points scored must be between 0 and {self.exam_name.out_of}."
            )
        super().clean()

    def _submission_is_locked(self, for_update=False):
        if not all((self.school_id, self.exam_name_id, self.subject_id, self.student_id)):
            return False
        enrollment = self.student
        submissions = MarksSubmission.unfiltered_objects.filter(
            school_id=self.school_id,
            exam_id=self.exam_name_id,
            classroom_id=enrollment.classroom_id,
            subject_id=self.subject_id,
            status__in=(
                MarksSubmission.Status.SUBMITTED,
                MarksSubmission.Status.APPROVED,
                MarksSubmission.Status.RELEASED,
            ),
        )
        if for_update:
            return submissions.select_for_update().first() is not None
        return submissions.exists()

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self._submission_is_locked(for_update=True):
                raise ValidationError(
                    "Marks cannot be changed while this submission is locked. "
                    "An authorized administrator must reopen it first."
                )
            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            if self._submission_is_locked(for_update=True):
                raise ValidationError(
                    "Marks cannot be deleted while this submission is locked. "
                    "An authorized administrator must reopen it first."
                )
            return super().delete(*args, **kwargs)


class MarksSubmission(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        RELEASED = "released", "Released"

    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="marks_submissions"
    )
    exam = models.ForeignKey(
        ExaminationListHandler,
        on_delete=models.CASCADE,
        related_name="mark_submissions",
    )
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.CASCADE, related_name="mark_submissions"
    )
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="mark_submissions"
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="marks_submitted",
    )
    submitted_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="marks_approved",
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    released_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SchoolScopedManager()
    unfiltered_objects = models.Manager()

    class Meta:
        ordering = ("exam__name", "classroom__name__name", "subject__name")
        constraints = [
            models.UniqueConstraint(
                fields=("school", "exam", "classroom", "subject"),
                name="unique_marks_submission_scope",
            )
        ]

    def __str__(self):
        return f"{self.exam} — {self.classroom} — {self.subject} ({self.status})"

    def clean(self):
        if (
            self.exam_id
            and self.classroom_id
            and not self.exam.classrooms.filter(pk=self.classroom_id).exists()
        ):
            raise ValidationError(
                {"classroom": "This exam is not assigned to the selected class."}
            )
        for related_object in (self.exam, self.classroom, self.subject):
            if related_object.school_id != self.school_id:
                raise ValidationError(
                    "The exam, class, subject, and submission must belong to one school."
                )


class MarksSubmissionEvent(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Created"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        RELEASED = "released", "Released"
        REOPENED = "reopened", "Reopened"

    submission = models.ForeignKey(
        MarksSubmission, on_delete=models.CASCADE, related_name="events"
    )
    action = models.CharField(max_length=12, choices=Action.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True
    )
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ("created_at", "pk")

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Submission history entries are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Submission history entries cannot be deleted.")
# rebuild trigger 20261019105406
