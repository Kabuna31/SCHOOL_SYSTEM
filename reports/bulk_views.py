"""Bulk report card generation — browser print to PDF."""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from academic.models import (
    ClassRoom,
    StudentClassEnrollment,
)
from administration.models import Term, School
from examination.models import MarksManagement
from portal.decorators import current_school

log = logging.getLogger(__name__)


def _require_staff(request):
    return bool(request.user.is_staff or request.user.is_superuser)


def _school(request):
    """Return the user's school, or None for superusers (cross-tenant)."""
    return current_school(request)


def _debug(request, where):
    u = request.user
    log.info(
        "[bulk_pdf:%s] email=%s is_staff=%s is_super=%s user.school=%s current_school=%s",
        where,
        getattr(u, "email", "?"),
        getattr(u, "is_staff", None),
        getattr(u, "is_superuser", None),
        getattr(u, "school", None),
        _school(request),
    )


@login_required
def bulk_pdf_picker(request):
    _debug(request, "picker")
    if not _require_staff(request):
        messages.error(request, "Staff access required.")
        return redirect("/")

    user = request.user
    is_super = user.is_superuser
    school = _school(request)

    # Non-superuser staff must have a school
    if school is None and not is_super:
        messages.error(request, "No school linked to your account.")
        return redirect("/")

    schools = None
    if school is None:
        # Superuser path — they pick a school first
        schools = School.objects.all().order_by("name")
        chosen_id = request.GET.get("school")
        if chosen_id:
            school = schools.filter(pk=chosen_id).first()

    classrooms = ClassRoom.objects.none()
    terms = Term.objects.none()

    if school is not None:
        classrooms = (
            ClassRoom.objects
            .filter(school=school)
            .select_related("name", "stream")
            .order_by("name__name", "stream__name")
        )
        terms = (
            Term.objects
            .filter(academic_year__school=school)
            .select_related("academic_year")
            .order_by("-academic_year__start_date", "-start_date")
        )

    return render(request, "reports/bulk_pdf_picker.html", {
        "school": school,
        "schools": schools,
        "classrooms": classrooms,
        "terms": terms,
    })


@login_required
def bulk_report_cards(request, classroom_id, term_id):
    _debug(request, "cards")
    if not _require_staff(request):
        messages.error(request, "Staff access required.")
        return redirect("/")

    user = request.user
    is_super = user.is_superuser
    school = _school(request)

    if school is None and not is_super:
        messages.error(request, "No school linked to your account.")
        return redirect("/")

    # Superuser with no school: look up by ID without school scoping
    classroom_qs = ClassRoom.objects.select_related("name", "stream")
    term_qs = Term.objects.select_related("academic_year")
    if school is not None:
        classroom_qs = classroom_qs.filter(school=school)
        term_qs = term_qs.filter(academic_year__school=school)

    classroom = get_object_or_404(classroom_qs, pk=classroom_id)
    term = get_object_or_404(term_qs, pk=term_id)

    # If superuser had no school, derive it from the classroom for downstream queries
    if school is None:
        school = classroom.school

    enrollments = (
        StudentClassEnrollment.objects
        .filter(
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
        rows, total = _collect_marks(school, term, enr)

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


def _collect_marks(school, term, enrollment):
    """Return (rows, total). Never raises — logs and returns empty on schema mismatch."""
    rows = []
    total = 0.0
    try:
        qs = (
            MarksManagement.objects
            .filter(student=enrollment)
            .select_related("subject", "exam_name")
            .order_by("subject__name")
        )
        if school is not None:
            try:
                qs = qs.filter(school=school)
            except Exception as e:
                log.warning("[bulk_pdf] school filter failed: %s", e)

        # Best-effort term filter
        try:
            qs = qs.filter(exam_name__term=term)
        except Exception as e:
            log.warning("[bulk_pdf] term filter failed: %s", e)

        for m in qs:
            exam = getattr(m, "exam_name", None)
            out_of = (
                getattr(exam, "out_of", None)
                or getattr(exam, "total", None)
                or getattr(exam, "max_score", None)
            )
            rows.append({
                "subject": getattr(getattr(m, "subject", None), "name", "—"),
                "exam": getattr(exam, "name", "—"),
                "score": m.points_scored,
                "out_of": out_of,
            })
            try:
                total += float(m.points_scored or 0)
            except (TypeError, ValueError):
                pass
    except Exception as e:
        log.exception("[bulk_pdf] _collect_marks failed: %s", e)
    return rows, total