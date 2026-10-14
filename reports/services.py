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


# Subjects that appear as "principal" (A Level) vs "subsidiary"
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
    """S5/S6 = A Level."""
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


# ---- Score assembly ----

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
    """Return {subject_id: MarksManagement} for one student, term, assessment_type."""
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
        # If more than one, keep highest
        existing = by_subject.get(m.subject_id)
        if existing is None or (m.points_scored or 0) > (existing.points_scored or 0):
            by_subject[m.subject_id] = m
    return by_subject, enrollment


def build_report(student, term):
    """Assemble the full report context for one student + one term."""
    class_level_name = student.class_level.name if student.class_level else ""
    alevel = is_a_level(class_level_name)

    aoi_marks, enrollment = _get_marks(student, term, "AOI")
    eot_marks, _ = _get_marks(student, term, "EOT")

    if enrollment is None:
        return None

    subject_ids = set(aoi_marks) | set(eot_marks)
    subjects = Subject.objects.filter(id__in=subject_ids).order_by("name")

    rows = []
    total_points = 0

    for subject in subjects:
        aoi = aoi_marks.get(subject.id)
        eot = eot_marks.get(subject.id)

        aoi_score = Decimal(str(aoi.points_scored)) if aoi else None
        eot_score = Decimal(str(eot.points_scored)) if eot else None

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
                points = ""
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
            "eot": _fmt_score(eot_score),
            "fs": _fmt_score(fs),
            "grade": grade,
            "loa": loa,
            "points": points,
            "tr": tr,
        })

    return {
        "student": student,
        "term": term,
        "classroom": enrollment.classroom,
        "is_a_level": alevel,
        "rows": rows,
        "total_points": total_points,
        "class_level_name": class_level_name,
    }


def _fmt_score(value):
    if value is None:
        return ""
    return str(int(value)) if Decimal(value) == int(value) else str(value)