from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

from academic.models import ClassRoom, Student, StudentClassEnrollment
from administration.models import School, Term

from .services import (
    build_report,
    compute_attendance_for_class,
    compute_class_positions,
    build_fee_statement,
    build_defaulters,
    build_class_marks_record,
)


def _current_school(request):
    user = request.user
    if hasattr(user, "school") and user.school:
        return user.school
    return School.objects.filter(active=True).first()


@staff_member_required
def reports_home(request):
    return render(request, "reports/home.html", {"title": "Reports"})


@staff_member_required
def report_card_picker(request):
    school = _current_school(request)
    terms = Term.objects.filter(academic_year__school=school).order_by("-start_date")
    classrooms = ClassRoom.objects.filter(school=school).order_by("name__name", "stream__name")
    assessment_type = request.GET.get("type", "EOT").upper()
    return render(request, "reports/report_card_picker.html", {
        "school": school,
        "terms": terms,
        "classrooms": classrooms,
        "assessment_type": assessment_type,
        "is_midterm": assessment_type == "AOI",
    })


@staff_member_required
def report_card(request, student_id, term_id):
    student = get_object_or_404(Student, pk=student_id)
    term = get_object_or_404(Term, pk=term_id)
    school = _current_school(request)

    mode = request.GET.get("type", "EOT").upper()
    if mode not in ("EOT", "AOI"):
        mode = "EOT"

    context = build_report(student, term, mode=mode)
    if context is None:
        return render(request, "reports/no_enrollment.html", {
            "student": student, "term": term,
        })

    context["school"] = school
    return render(request, "reports/report_card.html", context)


@staff_member_required
def marksheet_picker(request):
    school = _current_school(request)
    terms = Term.objects.filter(academic_year__school=school).order_by("-start_date")
    classrooms = ClassRoom.objects.filter(school=school).order_by("name__name", "stream__name")
    return render(request, "reports/marksheet_picker.html", {
        "school": school, "terms": terms, "classrooms": classrooms,
    })


@staff_member_required
def marksheet(request, classroom_id, term_id):
    school = _current_school(request)
    classroom = get_object_or_404(ClassRoom, pk=classroom_id, school=school)
    term = get_object_or_404(Term, pk=term_id)

    enrollments = (
        StudentClassEnrollment.objects
        .filter(classroom=classroom, academic_year=term.academic_year, student__isnull=False)
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )

    rows = []
    for e in enrollments:
        ctx = build_report(e.student, term, mode="EOT")
        if ctx:
            rows.append(ctx)

    return render(request, "reports/marksheet.html", {
        "school": school, "term": term, "classroom": classroom, "rows": rows,
    })


@staff_member_required
def analysis_picker(request):
    school = _current_school(request)
    terms = Term.objects.filter(academic_year__school=school).order_by("-start_date")
    classrooms = ClassRoom.objects.filter(school=school).order_by("name__name", "stream__name")
    return render(request, "reports/analysis_picker.html", {
        "school": school, "terms": terms, "classrooms": classrooms,
    })


@staff_member_required
def analysis(request, classroom_id, term_id):
    from collections import defaultdict

    school = _current_school(request)
    classroom = get_object_or_404(ClassRoom, pk=classroom_id, school=school)
    term = get_object_or_404(Term, pk=term_id)

    enrollments = (
        StudentClassEnrollment.objects
        .filter(classroom=classroom, academic_year=term.academic_year, student__isnull=False)
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )

    subject_stats = defaultdict(lambda: {
        "name": "", "scores": [], "A": 0, "B": 0, "C": 0, "D": 0, "E": 0,
    })
    student_averages = []

    for e in enrollments:
        ctx = build_report(e.student, term, mode="EOT")
        if not ctx:
            continue

        total_fs = 0
        count = 0
        for row in ctx["rows"]:
            if not row["fs"]:
                continue
            try:
                fs = float(row["fs"])
            except (TypeError, ValueError):
                continue

            stats = subject_stats[row["subject"]]
            stats["name"] = row["subject"]
            stats["scores"].append(fs)
            letter = row["grade"] or "?"
            if letter in ("A", "B", "C", "D", "E"):
                stats[letter] += 1

            total_fs += fs
            count += 1

        avg = round(total_fs / count, 1) if count else 0
        student_averages.append({
            "student": e.student,
            "average": avg,
            "count": count,
        })

    subjects = []
    for s in subject_stats.values():
        if not s["scores"]:
            continue
        s["mean"] = round(sum(s["scores"]) / len(s["scores"]), 1)
        s["sat"] = len(s["scores"])
        subjects.append(s)

    student_averages.sort(key=lambda x: -x["average"])
    for i, row in enumerate(student_averages):
        row["rank"] = i + 1

    return render(request, "reports/analysis.html", {
        "school": school,
        "term": term,
        "classroom": classroom,
        "subjects": subjects,
        "students": student_averages[:10],
    })


@staff_member_required
def generate_for_class(request, classroom_id, term_id):
    """Compute positions and attendance for a whole class."""
    school = _current_school(request)
    classroom = get_object_or_404(ClassRoom, pk=classroom_id, school=school)
    term = get_object_or_404(Term, pk=term_id)

    try:
        total = compute_class_positions(classroom, term)
        present_count = compute_attendance_for_class(classroom, term)
        messages.success(
            request,
            f"Generated {total} report cards with positions. "
            f"Processed {present_count} attendance records.",
        )
    except Exception as e:
        messages.error(request, f"Error: {e}")

    return redirect(f"/reports/report-card-picker/?classroom={classroom.id}&term={term.id}")



@staff_member_required
def fee_statement(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    school = _current_school(request)
    if student.school_id != school.id:
        return render(request, "reports/no_enrollment.html", {
            "student": student, "term": None,
        })

    context = build_fee_statement(student)
    context["school"] = school
    return render(request, "reports/fee_statement.html", context)


@staff_member_required
def defaulters(request):
    school = _current_school(request)
    rows = build_defaulters(school)
    return render(request, "reports/defaulters.html", {
        "school": school,
        "rows": rows,
        "total_owed": sum((r["total_owed"] for r in rows), Decimal("0.00")),
    })


@staff_member_required
def class_marks_record(request, classroom_id, term_id):
    school = _current_school(request)
    classroom = get_object_or_404(ClassRoom, pk=classroom_id, school=school)
    term = get_object_or_404(Term, pk=term_id)
    context = build_class_marks_record(classroom, term)
    context["school"] = school
    return render(request, "reports/class_marks_record.html", context)