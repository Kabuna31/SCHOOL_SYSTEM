from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from academic.models import (
    AllocatedSubject,
    StudentClassEnrollment,
)
from examination.models import (
    ExaminationListHandler,
    MarksManagement,
)

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

# ---------- Accountant ----------

def _current_accountant(request):
    user = request.user
    if hasattr(user, "accountant"):
        return user.accountant
    return None


@accountant_required
def accountant_home(request):
    from finance.models import Receipt, Payment
    from academic.models import Student
    from decimal import Decimal

    accountant = _current_accountant(request)
    school = current_school(request)

    if school is None:
        return render(request, "portal/no_accountant.html")

    today = timezone.now().date()
    month_start = today.replace(day=1)

    # KPIs
    receipts_today = Receipt.objects.filter(
        school=school, payment_date=today
    )
    receipts_month = Receipt.objects.filter(
        school=school, payment_date__gte=month_start
    )
    total_today = receipts_today.aggregate(s=models.Sum("amount"))["s"] or Decimal("0.00")
    total_month = receipts_month.aggregate(s=models.Sum("amount"))["s"] or Decimal("0.00")

    # Recent receipts
    recent = (
        Receipt.objects
        .filter(school=school)
        .select_related("student", "paid_for", "received_by")
        .order_by("-payment_date", "-id")[:20]
    )

    # Student lookup for payment entry
    students = Student.objects.filter(school=school).order_by("last_name", "first_name")[:500]

    return render(request, "portal/accountant_home.html", {
        "accountant": accountant,
        "school": school,
        "today": today,
        "receipts_today_count": receipts_today.count(),
        "total_today": total_today,
        "total_month": total_month,
        "recent": recent,
        "students": students,
    })


@accountant_required
def accountant_payment_add(request):
    from finance.models import (
        Receipt, ReceiptAllocation, PaymentThrough, PaymentStatus,
    )
    from academic.models import Student
    from decimal import Decimal

    school = current_school(request)
    if school is None:
        messages.error(request, "No school linked to your account.")
        return redirect("portal:accountant_home")

    allocations = ReceiptAllocation.objects.filter(school=school).order_by("name")
    students = Student.objects.filter(school=school).order_by("last_name", "first_name")
    accountant = _current_accountant(request)

    if request.method == "POST":
        student_id = request.POST.get("student")
        amount = request.POST.get("amount", "").strip()
        allocation_id = request.POST.get("paid_for")
        paid_through = request.POST.get("paid_through") or PaymentThrough.CASH
        payer = request.POST.get("payer", "").strip() or "Unknown"

        student = students.filter(pk=student_id).first()
        allocation = allocations.filter(pk=allocation_id).first()

        try:
            amount_dec = Decimal(amount)
            if amount_dec <= 0:
                raise ValueError("Amount must be positive.")
        except Exception:
            messages.error(request, "Invalid amount.")
            return redirect("portal:accountant_payment_add")

        if student is None:
            messages.error(request, "Please pick a student.")
            return redirect("portal:accountant_payment_add")

        receipt = Receipt.objects.create(
            school=school,
            payer=payer,
            paid_for=allocation,
            student=student,
            amount=amount_dec,
            paid_through=paid_through,
            status=PaymentStatus.COMPLETED,
            received_by=accountant,
        )
        messages.success(
            request,
            f"Receipt #{receipt.receipt_number} recorded for {student.full_name}."
        )
        return redirect("portal:accountant_home")

    return render(request, "portal/accountant_payment_add.html", {
        "school": school,
        "students": students,
        "allocations": allocations,
        "paid_through_choices": PaymentThrough.choices,
    })


@accountant_required
def accountant_receipts(request):
    from finance.models import Receipt

    school = current_school(request)
    if school is None:
        return render(request, "portal/no_accountant.html")

    qs = (
        Receipt.objects
        .filter(school=school)
        .select_related("student", "paid_for", "received_by")
        .order_by("-payment_date", "-id")
    )

    student_id = request.GET.get("student")
    date_from = request.GET.get("from")
    date_to = request.GET.get("to")

    if student_id:
        qs = qs.filter(student_id=student_id)
    if date_from:
        qs = qs.filter(payment_date__gte=date_from)
    if date_to:
        qs = qs.filter(payment_date__lte=date_to)

    from academic.models import Student
    students = Student.objects.filter(school=school).order_by("last_name", "first_name")

    return render(request, "portal/accountant_receipts.html", {
        "school": school,
        "receipts": qs[:200],
        "students": students,
        "selected_student": student_id,
        "date_from": date_from or "",
        "date_to": date_to or "",
    })

# ---------- Parent ----------

def _current_parent(request):
    user = request.user
    if hasattr(user, "academic_parent"):
        return user.academic_parent
    return None


@parent_required
def parent_home(request):
    from academic.models import Student
    from finance.models import DebtRecord
    from attendance.models import StudentAttendance
    from examination.models import MarksManagement
    from decimal import Decimal

    parent = _current_parent(request)
    if parent is None:
        return render(request, "portal/no_parent.html")

    children = (
        Student.objects
        .filter(parent_guardian=parent)
        .select_related("class_level", "class_of_year")
        .order_by("last_name", "first_name")
    )

    child_data = []
    for child in children:
        debts = DebtRecord.objects.filter(student=child, is_reversed=False)
        billed = sum((d.amount_added for d in debts), Decimal("0.00"))
        paid = sum((d.amount_paid for d in debts), Decimal("0.00"))
        balance = billed - paid

        recent_marks = (
            MarksManagement.objects
            .filter(student__student=child)
            .select_related("subject", "exam_name")
            .order_by("-date_time")[:10]
        )

        attendance = (
            StudentAttendance.objects
            .filter(student=child)
            .select_related("status")
            .order_by("-date")[:30]
        )
        absent_count = sum(
            1 for a in attendance if a.status and a.status.absent
        )

        child_data.append({
            "student": child,
            "billed": billed,
            "paid": paid,
            "balance": balance,
            "recent_marks": recent_marks,
            "absent_count": absent_count,
            "attendance_marked": len(attendance),
        })

    return render(request, "portal/parent_home.html", {
        "parent": parent,
        "children": child_data,
    })


@parent_required
def parent_child_detail(request, student_id):
    from academic.models import Student, StudentClassEnrollment
    from finance.models import DebtRecord, Receipt
    from attendance.models import StudentAttendance
    from examination.models import MarksManagement
    from decimal import Decimal

    parent = _current_parent(request)
    if parent is None:
        return render(request, "portal/no_parent.html")

    student = Student.objects.filter(pk=student_id, parent_guardian=parent).first()
    if student is None:
        messages.error(request, "That student isn't linked to your account.")
        return redirect("portal:parent_home")

    enrollment = (
        StudentClassEnrollment.objects
        .filter(student=student)
        .select_related("classroom", "classroom__name", "classroom__stream", "academic_year")
        .order_by("-academic_year__start_date")
        .first()
    )

    debts = (
        DebtRecord.objects
        .filter(student=student, is_reversed=False)
        .select_related("term", "term__academic_year")
        .order_by("-term__start_date")
    )
    billed = sum((d.amount_added for d in debts), Decimal("0.00"))
    paid = sum((d.amount_paid for d in debts), Decimal("0.00"))
    balance = billed - paid

    receipts = (
        Receipt.objects
        .filter(student=student)
        .order_by("-payment_date")[:20]
    )

    marks = (
        MarksManagement.objects
        .filter(student__student=student)
        .select_related("subject", "exam_name")
        .order_by("-date_time")[:30]
    )

    attendance = (
        StudentAttendance.objects
        .filter(student=student)
        .select_related("status")
        .order_by("-date")[:60]
    )
    absent_count = sum(1 for a in attendance if a.status and a.status.absent)

    return render(request, "portal/parent_child_detail.html", {
        "parent": parent,
        "student": student,
        "enrollment": enrollment,
        "debts": debts,
        "billed": billed,
        "paid": paid,
        "balance": balance,
        "receipts": receipts,
        "marks": marks,
        "attendance": attendance,
        "absent_count": absent_count,
    })