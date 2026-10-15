from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from academic.models import (
    AllocatedSubject,
    ClassRoom,
    StudentClassEnrollment,
    Subject,
)
from administration.models import Term, School
from attendance.models import AttendanceStatus, StudentAttendance
from examination.models import (
    ExaminationListHandler,
    MarksManagement,
)

from .decorators import (
    teacher_required,
    accountant_required,
    parent_required,
    current_teacher,
    current_school,
    portal_redirect,
)


# ---------- Login / Logout ----------

def portal_login(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(portal_redirect(request.user))

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(portal_redirect(user))
        messages.error(request, "Invalid email or password.")
    return render(request, "portal/login.html")


def portal_logout(request):
    logout(request)
    return redirect("portal:login")


# ---------- Teacher ----------

@teacher_required
def teacher_home(request):
    teacher = current_teacher(request)
    school = current_school(request)

    if teacher is None:
        return render(request, "portal/no_teacher.html")

    allocations = (
        AllocatedSubject.objects
        .filter(teacher_name=teacher, school=school)
        .select_related("subject", "class_room", "class_room__name", "class_room__stream", "term", "academic_year")
        .order_by("class_room__name__name", "class_room__stream__name", "subject__name")
    )

    return render(request, "portal/teacher_home.html", {
        "teacher": teacher,
        "allocations": allocations,
        "school": school,
    })


@teacher_required
def teacher_marks_entry(request, allocation_id):
    allocation = get_object_or_404(AllocatedSubject, pk=allocation_id)
    teacher = current_teacher(request)
    if allocation.teacher_name_id != teacher.id and not request.user.is_superuser:
        messages.error(request, "You are not assigned to this subject.")
        return redirect("portal:teacher_home")

    term = allocation.term or Term.objects.filter(
        academic_year=allocation.academic_year
    ).order_by("-start_date").first()

    if term is None:
        messages.error(request, "No term found for this allocation.")
        return redirect("portal:teacher_home")

    exams = ExaminationListHandler.objects.filter(
        school=allocation.school,
        term=term,
        classrooms=allocation.class_room,
    ).order_by("name")

    selected_exam = None
    if request.method == "POST":
        exam_id = request.POST.get("exam_id")
        selected_exam = exams.filter(pk=exam_id).first()

        if selected_exam:
            enrollments = StudentClassEnrollment.objects.filter(
                classroom=allocation.class_room,
                academic_year=allocation.academic_year,
                student__isnull=False,
            ).select_related("student").order_by("student__last_name")

            saved = 0
            for enrollment in enrollments:
                score_field = f"score_{enrollment.pk}"
                raw = request.POST.get(score_field, "").strip()
                if raw == "":
                    continue
                try:
                    score = float(raw)
                except ValueError:
                    continue
                if score < 0 or score > selected_exam.out_of:
                    continue

                MarksManagement.objects.update_or_create(
                    school=allocation.school,
                    exam_name=selected_exam,
                    subject=allocation.subject,
                    student=enrollment,
                    defaults={
                        "points_scored": score,
                        "created_by": teacher,
                    },
                )
                saved += 1

            messages.success(request, f"Saved {saved} marks.")
            return redirect("portal:teacher_marks_entry", allocation_id=allocation.id)

    enrollments = StudentClassEnrollment.objects.filter(
        classroom=allocation.class_room,
        academic_year=allocation.academic_year,
        student__isnull=False,
    ).select_related("student").order_by("student__last_name")

    existing_marks = {}
    if selected_exam:
        for m in MarksManagement.objects.filter(
            exam_name=selected_exam,
            subject=allocation.subject,
            student__in=enrollments,
        ):
            existing_marks[m.student_id] = m.points_scored

    rows = []
    for e in enrollments:
        rows.append({
            "enrollment": e,
            "student": e.student,
            "score": existing_marks.get(e.pk, ""),
        })

    return render(request, "portal/teacher_marks_entry.html", {
        "allocation": allocation,
        "exams": exams,
        "selected_exam": selected_exam,
        "rows": rows,
        "term": term,
    })


@teacher_required
def teacher_attendance(request, allocation_id):
    allocation = get_object_or_404(AllocatedSubject, pk=allocation_id)
    teacher = current_teacher(request)
    if allocation.teacher_name_id != teacher.id and not request.user.is_superuser:
        messages.error(request, "You are not assigned to this subject.")
        return redirect("portal:teacher_home")

    today = timezone.now().date()
    statuses = AttendanceStatus.objects.all()

    if request.method == "POST":
        date_str = request.POST.get("date", today.isoformat())
        saved = 0
        enrollments = StudentClassEnrollment.objects.filter(
            classroom=allocation.class_room,
            academic_year=allocation.academic_year,
            student__isnull=False,
        ).select_related("student")

        for e in enrollments:
            status_id = request.POST.get(f"status_{e.pk}")
            if not status_id:
                continue
            status = statuses.filter(pk=status_id).first()
            if not status:
                continue

            present, _ = AttendanceStatus.objects.get_or_create(name="Present")
            if status == present:
                # Don't save Present — same rule as the model
                StudentAttendance.objects.filter(
                    student=e.student, date=date_str
                ).delete()
                continue

            StudentAttendance.objects.update_or_create(
                student=e.student,
                date=date_str,
                ClassRoom=allocation.class_room,
                defaults={"status": status},
            )
            saved += 1

        messages.success(request, f"Attendance saved for {saved} students.")
        return redirect("portal:teacher_attendance", allocation_id=allocation.id)

    enrollments = StudentClassEnrollment.objects.filter(
        classroom=allocation.class_room,
        academic_year=allocation.academic_year,
        student__isnull=False,
    ).select_related("student").order_by("student__last_name")

    return render(request, "portal/teacher_attendance.html", {
        "allocation": allocation,
        "enrollments": enrollments,
        "statuses": statuses,
        "today": today,
    })


# ---------- Accountant / Parent stubs (v0.8.2, v0.8.3) ----------

@accountant_required
def accountant_home(request):
    return render(request, "portal/accountant_home.html")


@parent_required
def parent_home(request):
    return render(request, "portal/parent_home.html")