from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render

from academic.models import ClassRoom, Student, StudentClassEnrollment
from administration.models import School, Term

from .services import build_report


def _current_school(request):
    user = request.user
    if hasattr(user, "school") and user.school:
        return user.school
    return School.objects.filter(active=True).first()


@staff_member_required
def reports_home(request):
    school = _current_school(request)
    terms = Term.objects.filter(academic_year__school=school).order_by("-start_date")
    classrooms = ClassRoom.objects.filter(school=school).order_by("name__name", "stream__name")
    return render(request, "reports/home.html", {
        "school": school,
        "terms": terms,
        "classrooms": classrooms,
    })


@staff_member_required
def report_card(request, student_id, term_id):
    student = get_object_or_404(Student, pk=student_id)
    term = get_object_or_404(Term, pk=term_id)
    school = _current_school(request)

    context = build_report(student, term)
    if context is None:
        return render(request, "reports/no_enrollment.html", {
            "student": student, "term": term,
        })

    context["school"] = school
    return render(request, "reports/report_card.html", context)


@staff_member_required
def report_card_print(request, student_id, term_id):
    return report_card(request, student_id, term_id)


@staff_member_required
def bulk_report_cards(request, classroom_id, term_id):
    school = _current_school(request)
    classroom = get_object_or_404(ClassRoom, pk=classroom_id, school=school)
    term = get_object_or_404(Term, pk=term_id)

    enrollments = (
        StudentClassEnrollment.objects
        .filter(classroom=classroom, academic_year=term.academic_year, student__isnull=False)
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )

    reports = []
    for e in enrollments:
        ctx = build_report(e.student, term)
        if ctx:
            ctx["school"] = school
            reports.append(ctx)

    return render(request, "reports/bulk_report_cards.html", {
        "school": school,
        "term": term,
        "classroom": classroom,
        "reports": reports,
    })