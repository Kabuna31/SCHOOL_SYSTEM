"""Data assembly for report cards — O Level and A Level."""
from decimal import Decimal, ROUND_HALF_UP

from academic.models import (
    ClassRoom,
    Student,
    StudentClassEnrollment,
    Subject,
    Teacher,
)
from administration.models import Term
from examination.models import (
    ExaminationListHandler,
    MarksManagement,
)


SUBSIDIARY_NAMES = {
    "general paper",
    "sub math",
    "sub ict",
    "sub ict ",
    "subsidiary math",
    "subsidiary ict",
    "subsidiary mathematics",
}


def is_a_level(class_level_name: str) -> bool:
    if not class_level_name:
        return False
    name = class_level_name.upper().replace(".", "").strip()
    return name.startswith("S5") or name.startswith("S6")


def is_subsidiary(subject_name: str) -> bool:
    return (subject_name or "").lower().strip() in SUBSIDIARY_NAMES


# ---- Grade tables ----

O_LEVEL_BANDS = [
    (Decimal("80"), Decimal("100"), "A", "Exceptional"),
    (Decimal("70"), Decimal("79.99"), "B", "Outstanding"),
    (Decimal("60"), Decimal("69.99"), "C", "Satisfactory"),
    (Decimal("50"), Decimal("59.99"), "D", "Basic"),
    (Decimal("0"), Decimal("49.99"), "E", "Elementary"),
]

A_LEVEL_BANDS = [
    (Decimal("80"), Decimal("100"), "A", "Exceptional", 6),
    (Decimal("70"), Decimal("79.99"), "B", "Outstanding", 5),
    (Decimal("60"), Decimal("69.99"), "C", "Satisfactory", 4),
    (Decimal("50"), Decimal("59.99"), "D", "Basic", 3),
    (Decimal("40"), Decimal("49.99"), "E", "Elementary", 2),
    (Decimal("35"), Decimal("39.99"), "O", "Subsidiary Pass", 1),
    (Decimal("0"), Decimal("34.99"), "F", "Fail", 0),
]

SUBSIDIARY_BANDS = [
    (Decimal("80"), Decimal("100"), "D1", "Distinction 1"),
    (Decimal("70"), Decimal("79.99"), "D2", "Distinction 2"),
    (Decimal("65"), Decimal("69.99"), "C3", "Credit 3"),
    (Decimal("60"), Decimal("64.99"), "C4", "Credit 4"),
    (Decimal("55"), Decimal("59.99"), "C5", "Credit 5"),
    (Decimal("50"), Decimal("54.99"), "C6", "Credit 6"),
    (Decimal("45"), Decimal("49.99"), "P7", "Pass 7"),
    (Decimal("40"), Decimal("44.99"), "P8", "Pass 8"),
    (Decimal("0"), Decimal("39.99"), "F9", "Fail 9"),
]


def _round2(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def grade_o_level(fs):
    if fs is None:
        return "", ""
    fs = Decimal(str(fs))
    for lo, hi, letter, loa in O_LEVEL_BANDS:
        if lo <= fs <= hi:
            return letter, loa
    return "", ""


def grade_a_level(fs):
    if fs is None:
        return "", "", ""
    fs = Decimal(str(fs))
    for lo, hi, letter, loa, points in A_LEVEL_BANDS:
        if lo <= fs <= hi:
            return letter, loa, str(points)
    return "", "", ""


def grade_subsidiary(fs):
    if fs is None:
        return "", ""
    fs = Decimal(str(fs))
    for lo, hi, letter, desc in SUBSIDIARY_BANDS:
        if lo <= fs <= hi:
            return letter, desc
    return "", ""


def _teacher_initials(teacher):
    if teacher is None:
        return ""
    short = (getattr(teacher, "short_name", "") or "").strip()
    if short:
        return short.upper()
    first = (teacher.first_name or "")[:1]
    last = (teacher.last_name or "")[:1]
    return (first + last).upper()


def _get_marks(student, term, assessment_type):
    enrollment = StudentClassEnrollment.objects.filter(
        student=student, academic_year=term.academic_year
    ).first()
    if enrollment is None:
        return {}, None

    exams = ExaminationListHandler.objects.filter(
        term=term,
        assessment_type=assessment_type,
        classrooms=enrollment.classroom,
    )
    marks = MarksManagement.objects.filter(
        student=enrollment,
        exam_name__in=exams,
    ).select_related("subject", "created_by", "exam_name")

    by_subject = {}
    for m in marks:
        existing = by_subject.get(m.subject_id)
        if existing is None or (m.points_scored or 0) > (existing.points_scored or 0):
            by_subject[m.subject_id] = m
    return by_subject, enrollment


def _fmt_score(value):
    if value is None:
        return ""
    return str(int(value)) if Decimal(value) == int(value) else str(value)


def _count_attendance(student, term):
    try:
        from attendance.models import StudentAttendance
    except ImportError:
        return None, None

    records = StudentAttendance.objects.filter(
        student=student,
        date__gte=term.start_date,
        date__lte=term.end_date,
    ).select_related("status")

    days_absent = 0
    for r in records:
        s = r.status
        if s is None:
            continue
        if s.absent or (s.absent is False and s.half):
            days_absent += 0.5 if s.half else 1

    return None, int(days_absent) if days_absent else 0


def build_report(student, term, mode="EOT"):
    from .models import ReportCard
    from .comment_engine import generate_comment

    class_level_name = student.class_level.name if student.class_level else ""
    alevel = is_a_level(class_level_name)

    aoi_marks, enrollment = _get_marks(student, term, "AOI")
    eot_marks, _ = _get_marks(student, term, "EOT")

    if enrollment is None:
        return None

    is_midterm = (mode == "AOI")
    subject_ids = set(aoi_marks) | (set() if is_midterm else set(eot_marks))
    subjects = Subject.objects.filter(id__in=subject_ids).order_by("name")

    rows = []
    total_points = 0
    total_fs = Decimal("0")
    sat = 0

    for subject in subjects:
        aoi = aoi_marks.get(subject.id)
        eot = None if is_midterm else eot_marks.get(subject.id)

        aoi_score = Decimal(str(aoi.points_scored)) if aoi else None
        eot_score = Decimal(str(eot.points_scored)) if eot else None

        if is_midterm:
            fs = _round2(aoi_score) if aoi_score is not None else None
        else:
            if aoi_score is None and eot_score is None:
                fs = None
            elif aoi_score is None:
                fs = _round2(eot_score)
            elif eot_score is None:
                fs = _round2(aoi_score)
            else:
                fs = _round2(aoi_score * Decimal("0.2") + eot_score * Decimal("0.8"))

        grade, loa, points = "", "", ""

        if alevel:
            if is_subsidiary(subject.name):
                grade, loa = grade_subsidiary(fs)
            else:
                grade, loa, points = grade_a_level(fs)
                if points:
                    total_points += int(points)
        else:
            grade, loa = grade_o_level(fs)

        tr = _teacher_initials((aoi or eot).created_by if (aoi or eot) else None)

        rows.append({
            "subject": subject.name.title(),
            "aoi": _fmt_score(aoi_score),
            "eot": "" if is_midterm else _fmt_score(eot_score),
            "fs": _fmt_score(fs),
            "grade": grade,
            "loa": loa,
            "points": points,
            "tr": tr,
        })

        if fs is not None:
            total_fs += fs
            sat += 1

    average = _round2(total_fs / sat) if sat else None

    rc = ReportCard.get_for(student, term)

    if not rc.general_grade and average is not None:
        if alevel:
            rc.general_grade = grade_a_level(average)[0]
        else:
            rc.general_grade = grade_o_level(average)[0]

    if not rc.general_comment:
        rc.general_comment = generate_comment(average, alevel)

    rc.save()

    _present, _absent = _count_attendance(student, term)
    class_teacher_comment = (
        rc.class_teacher_comment
        or getattr(enrollment.classroom.class_teacher, "short_name", "")
        or student.school.default_class_teacher_comment
        or ""
    )
    head_teacher_comment = (
        rc.head_teacher_comment
        or student.school.default_head_teacher_comment
        or ""
    )

    class_teacher = enrollment.classroom.class_teacher

    return {
        "student": student,
        "term": term,
        "classroom": enrollment.classroom,
        "is_a_level": alevel,
        "is_midterm": is_midterm,
        "rows": rows,
        "total_points": total_points,
        "class_level_name": class_level_name,
        "average": average,
        "sat": sat,
        "rc": rc,
        "class_teacher_comment": class_teacher_comment,
        "general_comment": rc.general_comment,
        "head_teacher_comment": head_teacher_comment,
        "general_grade": rc.general_grade,
        "position_display": rc.position_display,
        "attendance_summary": rc.attendance_summary,
        "class_teacher": class_teacher,
    }


def compute_class_positions(classroom, term):
    from .models import ReportCard

    enrollments = StudentClassEnrollment.objects.filter(
        classroom=classroom, academic_year=term.academic_year, student__isnull=False
    ).select_related("student")

    totals = []
    for e in enrollments:
        ctx = build_report(e.student, term, mode="EOT")
        if not ctx or ctx["average"] is None:
            continue
        totals.append((e.student, float(ctx["average"])))

    totals.sort(key=lambda x: -x[1])
    total = len(totals)

    for i, (student, avg) in enumerate(totals):
        rc = ReportCard.get_for(student, term)
        rc.position_in_class = i + 1
        rc.out_of_class = total
        rc.save()

    return total


def compute_attendance_for_class(classroom, term):
    from .models import ReportCard

    enrollments = StudentClassEnrollment.objects.filter(
        classroom=classroom, academic_year=term.academic_year, student__isnull=False
    ).select_related("student")

    count = 0
    for e in enrollments:
        present, absent = _count_attendance(e.student, term)
        rc = ReportCard.get_for(e.student, term)
        if present is not None:
            rc.days_present = present
        if absent is not None:
            rc.days_absent = absent
        rc.save()
        count += 1
    return count


# ---- FEE ----

def build_fee_statement(student):
    from finance.models import DebtRecord, PaymentRecord

    debts = (
        DebtRecord.objects
        .filter(student=student, is_reversed=False)
        .select_related("term", "term__academic_year")
        .order_by("term__academic_year__start_date", "term__start_date")
    )

    rows = []
    grand_total_due = Decimal("0.00")
    grand_total_paid = Decimal("0.00")

    for debt in debts:
        payments = (
            PaymentRecord.objects
            .filter(debt_record=debt)
            .select_related("receipt")
            .order_by("paid_on")
        )
        total_paid = sum((p.amount for p in payments), Decimal("0.00"))
        balance = debt.amount_added - total_paid

        rows.append({
            "term": debt.term,
            "amount_added": debt.amount_added,
            "total_paid": total_paid,
            "balance": balance,
            "payments": [
                {
                    "date": p.paid_on,
                    "amount": p.amount,
                    "method": p.method or "—",
                    "reference": p.reference or "—",
                    "receipt": p.receipt.receipt_number if p.receipt else "—",
                }
                for p in payments
            ],
        })

        grand_total_due += debt.amount_added
        grand_total_paid += total_paid

    return {
        "student": student,
        "rows": rows,
        "grand_total_due": grand_total_due,
        "grand_total_paid": grand_total_paid,
        "grand_balance": grand_total_due - grand_total_paid,
    }


def build_defaulters(school):
    from finance.models import DebtRecord

    debts = (
        DebtRecord.objects
        .filter(school=school, is_reversed=False)
        .select_related("student", "student__class_level", "term")
        .order_by("student__last_name", "student__first_name")
    )

    by_student = {}
    for debt in debts:
        balance = debt.balance
        if balance <= 0:
            continue
        key = debt.student_id
        if key not in by_student:
            by_student[key] = {
                "student": debt.student,
                "terms": [],
                "total_owed": Decimal("0.00"),
            }
        by_student[key]["terms"].append({
            "term": debt.term,
            "amount_added": debt.amount_added,
            "amount_paid": debt.amount_paid,
            "balance": balance,
        })
        by_student[key]["total_owed"] += balance

    return sorted(by_student.values(), key=lambda x: -x["total_owed"])


def build_class_marks_record(classroom, term):
    from academic.models import Subject as _S

    enrollments = (
        StudentClassEnrollment.objects
        .filter(classroom=classroom, academic_year=term.academic_year, student__isnull=False)
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )

    exams = ExaminationListHandler.objects.filter(term=term, classrooms=classroom)
    subject_ids = (
        MarksManagement.objects
        .filter(student__in=[e.id for e in enrollments], exam_name__in=exams)
        .values_list("subject_id", flat=True)
        .distinct()
    )
    subjects = list(_S.objects.filter(id__in=subject_ids).order_by("name"))

    marks_by_enrollment_subject = {}
    for m in MarksManagement.objects.filter(
        student__in=[e.id for e in enrollments], exam_name__in=exams
    ).select_related("exam_name"):
        key = (m.student_id, m.subject_id, m.exam_name.assessment_type)
        marks_by_enrollment_subject[key] = float(m.points_scored or 0)

    rows = []
    for e in enrollments:
        row = {"student": e.student, "cells": []}
        for s in subjects:
            aoi = marks_by_enrollment_subject.get((e.id, s.id, "AOI"))
            eot = marks_by_enrollment_subject.get((e.id, s.id, "EOT"))
            if aoi is None and eot is None:
                fs = None
            elif aoi is None:
                fs = eot
            elif eot is None:
                fs = aoi
            else:
                fs = round(aoi * 0.2 + eot * 0.8, 1)
            row["cells"].append({
                "subject": s.name.title(),
                "aoi": aoi if aoi is not None else "",
                "eot": eot if eot is not None else "",
                "fs": fs if fs is not None else "",
            })
        rows.append(row)

    return {
        "classroom": classroom,
        "term": term,
        "subjects": subjects,
        "rows": rows,
    }