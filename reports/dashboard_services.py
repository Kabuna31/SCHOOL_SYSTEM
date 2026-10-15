"""Aggregate data for the school dashboard."""
from decimal import Decimal

from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone

from academic.models import (
    ClassLevel,
    ClassRoom,
    Student,
    StudentClassEnrollment,
    Teacher,
)
from administration.models import AcademicYear, School, Term
from attendance.models import StudentAttendance
from finance.models import DebtRecord, PaymentRecord, Receipt
from examination.models import MarksManagement


def _active_school(request):
    user = request.user
    if hasattr(user, "school") and user.school:
        return user.school
    return School.objects.filter(active=True).first()


def _pick_term(school, term_id=None):
    if not school:
        return None
    qs = Term.objects.filter(academic_year__school=school).order_by("-start_date")
    if term_id:
        return qs.filter(pk=term_id).first() or qs.first()
    return qs.first()


def build_dashboard_context(request, term_id=None):
    school = _active_school(request)
    if not school:
        return {"school": None}

    term = _pick_term(school, term_id)
    terms = list(Term.objects.filter(academic_year__school=school).order_by("-start_date"))

    # ---- KPIs ----
    total_students = Student.objects.filter(school=school).count()
    total_teachers = Teacher.objects.filter(school=school, inactive=False).count()
    total_classes = ClassRoom.objects.filter(school=school).count()

    # ---- Enrolment by class level ----
    by_class_level = list(
        Student.objects
        .filter(school=school, class_level__isnull=False)
        .values("class_level__name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # ---- Gender split ----
    by_gender = list(
        Student.objects
        .filter(school=school)
        .values("gender")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # ---- Fee collection (per selected term) ----
    total_billed = Decimal("0.00")
    total_paid = Decimal("0.00")
    defaulters_count = 0
    total_owed = Decimal("0.00")

    if term:
        debts = (
            DebtRecord.objects
            .filter(school=school, term=term, is_reversed=False)
        )
        total_billed = debts.aggregate(s=Sum("amount_added"))["s"] or Decimal("0.00")
        total_paid = debts.aggregate(s=Sum("amount_paid"))["s"] or Decimal("0.00")

        defaulters = debts.filter(amount_added__gt=0).filter(
            amount_paid__lt=models.F("amount_added")
        ) if False else None

        # Count defaulters manually
        for debt in debts:
            if debt.amount_paid < debt.amount_added:
                defaulters_count += 1
                total_owed += (debt.amount_added - debt.amount_paid)

    # ---- Attendance (per selected term) ----
    attendance_total = 0
    attendance_absent = 0
    if term:
        records = StudentAttendance.objects.filter(
            student__school=school,
            date__gte=term.start_date,
            date__lte=term.end_date,
        ).select_related("status")
        attendance_total = records.count()
        for r in records:
            if r.status and r.status.absent:
                attendance_absent += 1

    # ---- Recent activity ----
    recent_receipts = (
        Receipt.objects
        .filter(school=school)
        .select_related("student")
        .order_by("-date")[:5]
        if hasattr(Receipt, "date") else []
    )

    recent_marks = (
        MarksManagement.objects
        .filter(school=school)
        .select_related("student__student", "subject")
        .order_by("-date_time")[:5]
    )

    return {
        "school": school,
        "term": term,
        "terms": terms,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "by_class_level": by_class_level,
        "by_gender": by_gender,
        "total_billed": total_billed,
        "total_paid": total_paid,
        "total_owed": total_owed,
        "defaulters_count": defaulters_count,
        "attendance_total": attendance_total,
        "attendance_absent": attendance_absent,
        "recent_receipts": recent_receipts,
        "recent_marks": recent_marks,
    }