"""Bulk report card generation — browser print to PDF."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from academic.models import (
    ClassRoom,
    StudentClassEnrollment,
)
from administration.models import Term
from examination.models import MarksManagement
from portal.decorators import current_school


def _require_staff(request):
    return request.user.is_staff or request.user.is_superuser


def _school(request):
    """Reuse the portal's existing current_school helper."""
    return current_school(request)


@login_required
def bulk_pdf_picker(request):
    """Choose classroom + term."""
    if not _require_staff(request):
        messages.error(request, "Staff access required.")
        return redirect("/")

    school = _school(request)
    if school is None:
        messages.error(request, "No school linked to your account.")
        return redirect("/")

    classrooms = (
        ClassRoom.objects
        .filter(school=school)
        .select_related("name", "stream")                 # name IS the ClassLevel
        .order_by("name__name", "stream__name")           # level name, stream name
    )

    terms = (
        Term.objects
        .filter(academic_year__school=school)
        .select_related("academic_year")
        .order_by("-academic_year__start_date", "-start_date")   # VERIFY field names
    )

    return render(request, "reports/bulk_pdf_picker.html", {
        "school": school,
        "classrooms": classrooms,
        "terms": terms,
    })


@login_required
def bulk_report_cards(request, classroom_id, term_id):
    """Render every student's report card on one page for printing."""
    if not _require_staff(request):
        messages.error(request, "Staff access required.")
        return redirect("/")

    school = _school(request)
    if school is None:
        messages.error(request, "No school linked to your account.")
        return redirect("/")

    classroom = get_object_or_404(
        ClassRoom.objects.select_related("name", "stream"),
        pk=classroom_id, school=school,
    )
    term = get_object_or_404(
        Term.objects.select_related("academic_year"),
        pk=term_id, academic_year__school=school,
    )

    enrollments = (
        StudentClassEnrollment.objects
        .filter(
            school=school,
            classroom=classroom,
            academic_year=term.academic_year,
            student__isnull=False,
        )
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )

    students_data = []
    for enr in enrollments:
        student = enr.student

        # VERIFY: adjust field names once we know the MarksManagement schema
        marks = (
            MarksManagement.objects
            .filter(
                school=school,
                student=enr,               # VERIFY: points to StudentClassEnrollment or Student?
                exam_name__term=term,      # VERIFY: does ExamName have .term FK?
            )
            .select_related("subject", "exam_name")
            .order_by("subject__name")
        )

        rows = []
        total = 0.0
        for m in marks:
            rows.append({
                "subject": m.subject.name,
                "exam": m.exam_name.name,
                "score": m.points_scored,
                "out_of": m.exam_name.out_of,   # VERIFY: is it .out_of or .total?
            })
            total += float(m.points_scored or 0)

        students_data.append({
            "student": student,
            "enrollment": enr,
            "rows": rows,
            "total": round(total, 2),
            "average": round(total / len(rows), 2) if rows else 0,
        })

    return render(request, "reports/bulk_report_cards.html", {
        "school": school,
        "classroom": classroom,
        "term": term,
        "students": students_data,
        "generated_at": timezone.now(),
    })