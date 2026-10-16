"""Bulk operations: student import with preview and error reporting."""
import csv
import io

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone

from academic.models import (
    ClassLevel,
    ClassYear,
    Parent,
    Student,
)
from administration.models import School

from .decorators import accountant_required, current_school


# Expected CSV columns
REQUIRED_COLUMNS = ["first_name", "last_name", "parent_contact"]
OPTIONAL_COLUMNS = [
    "middle_name", "gender", "religion", "date_of_birth",
    "class_level", "class_of_year", "admission_number",
    "prems_number", "std_vii_number", "region", "city", "street", "blood_group",
]
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


def _require_admin(request):
    user = request.user
    if not (user.is_superuser or user.is_staff):
        messages.error(request, "Admin access required.")
        return False
    return True


@accountant_required
def bulk_students_upload(request):
    """Upload a CSV, validate every row, show preview."""
    if not _require_admin(request):
        return redirect("portal:home" if False else "portal:accountant_home")

    school = current_school(request)
    if school is None:
        messages.error(request, "No school linked to your account.")
        return redirect("portal:accountant_home")

    if request.method == "POST":
        uploaded = request.FILES.get("csv_file")
        if not uploaded:
            messages.error(request, "Please choose a CSV file.")
            return redirect("portal:bulk_students_upload")

        if not uploaded.name.lower().endswith(".csv"):
            messages.error(request, "Only .csv files are supported.")
            return redirect("portal:bulk_students_upload")

        try:
            text = uploaded.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            messages.error(request, "File must be UTF-8 encoded.")
            return redirect("portal:bulk_students_upload")

        reader = csv.DictReader(io.StringIO(text))

        # Check required columns
        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        missing = [c for c in REQUIRED_COLUMNS if c not in headers]
        if missing:
            messages.error(
                request,
                f"Missing required columns: {', '.join(missing)}. "
                f"Download the sample CSV for the correct format."
            )
            return redirect("portal:bulk_students_upload")

        # Validate each row
        valid_rows = []
        error_rows = []

        for i, raw in enumerate(reader, start=2):  # row 2 in Excel
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
            errors = []

            # Required fields
            if not row.get("first_name"):
                errors.append("first_name is required")
            if not row.get("last_name"):
                errors.append("last_name is required")
            if not row.get("parent_contact"):
                errors.append("parent_contact is required")

            # Lookups
            class_level = None
            if row.get("class_level"):
                class_level = ClassLevel.objects.filter(
                    school=school, name__iexact=row["class_level"]
                ).first()
                if class_level is None:
                    errors.append(f"Class level '{row['class_level']}' not found")

            class_of_year = None
            if row.get("class_of_year"):
                class_of_year = ClassYear.objects.filter(
                    school=school, year__iexact=row["class_of_year"]
                ).first()
                if class_of_year is None:
                    errors.append(f"Class year '{row['class_of_year']}' not found")

            # Duplicate check
            if row.get("admission_number"):
                if Student.objects.filter(
                    school=school, admission_number=row["admission_number"]
                ).exists():
                    errors.append(
                        f"Admission number '{row['admission_number']}' already exists"
                    )

            # Normalize gender
            gender = (row.get("gender") or "").strip().upper()[:1]
            if gender and gender not in ("M", "F"):
                errors.append("gender must be M or F")

            row["_class_level_obj"] = class_level
            row["_class_of_year_obj"] = class_of_year
            row["_gender_normalized"] = gender
            row["_line"] = i

            if errors:
                row["_errors"] = errors
                error_rows.append(row)
            else:
                valid_rows.append(row)

        # Store in session for the confirm step
        request.session["bulk_students_valid"] = [
            {k: v for k, v in r.items() if not k.startswith("_")} | {
                "_class_level_id": r["_class_level_obj"].id if r["_class_level_obj"] else None,
                "_class_of_year_id": r["_class_of_year_obj"].id if r["_class_of_year_obj"] else None,
                "_gender_normalized": r["_gender_normalized"],
            }
            for r in valid_rows
        ]
        request.session["bulk_students_errors"] = [
            {k: v for k, v in r.items() if not k.startswith("_")} | {"_errors": r["_errors"], "_line": r["_line"]}
            for r in error_rows
        ]

        return render(request, "portal/bulk_students_preview.html", {
            "school": school,
            "valid_count": len(valid_rows),
            "error_count": len(error_rows),
            "valid_rows": valid_rows[:50],
            "error_rows": error_rows[:50],
            "total_valid": len(valid_rows),
            "total_error": len(error_rows),
        })

    return render(request, "portal/bulk_students_upload.html", {
        "school": school,
        "required_columns": REQUIRED_COLUMNS,
        "optional_columns": OPTIONAL_COLUMNS,
    })


@accountant_required
def bulk_students_confirm(request):
    """Commit the validated rows to the DB."""
    if not _require_admin(request):
        return redirect("portal:accountant_home")

    school = current_school(request)
    if school is None:
        messages.error(request, "No school linked to your account.")
        return redirect("portal:accountant_home")

    rows = request.session.get("bulk_students_valid") or []
    if not rows:
        messages.error(request, "No valid rows to import. Please upload a CSV again.")
        return redirect("portal:bulk_students_upload")

    created = 0
    failed = []

    for i, row in enumerate(rows, start=1):
        try:
            class_level = None
            if row.get("_class_level_id"):
                class_level = ClassLevel.objects.filter(pk=row["_class_level_id"]).first()

            class_of_year = None
            if row.get("_class_of_year_id"):
                class_of_year = ClassYear.objects.filter(pk=row["_class_of_year_id"]).first()

            Student.objects.create(
                school=school,
                first_name=row.get("first_name") or "",
                middle_name=row.get("middle_name") or "",
                last_name=row.get("last_name") or "",
                parent_contact=row.get("parent_contact") or "",
                admission_number=row.get("admission_number") or "",
                prems_number=row.get("prems_number") or "",
                std_vii_number=row.get("std_vii_number") or "",
                region=row.get("region") or "",
                city=row.get("city") or "",
                street=row.get("street") or "",
                blood_group=row.get("blood_group") or "",
                religion=(row.get("religion") or "").lower() or None,
                gender=row.get("_gender_normalized") or None,
                date_of_birth=row.get("date_of_birth") or None,
                class_level=class_level,
                class_of_year=class_of_year,
            )
            created += 1
        except Exception as e:
            failed.append({"row": i, "error": str(e)})

    # Clear the session
    request.session.pop("bulk_students_valid", None)
    request.session.pop("bulk_students_errors", None)

    return render(request, "portal/bulk_students_result.html", {
        "school": school,
        "created": created,
        "failed": failed,
    })


@accountant_required
def bulk_students_sample(request):
    """Download a sample CSV template."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="students-sample.csv"'

    writer = csv.writer(response)
    writer.writerow(ALL_COLUMNS)
    writer.writerow([
        "John", "Doe", "M", "M", "Christian", "2010-01-15",
        "S.1", "2026", "STU-001", "", "", "Central", "Kampala", "Nakasero", "O+",
        "0700000001",
    ])
    writer.writerow([
        "Jane", "Doe", "F", "F", "Christian", "2011-03-22",
        "S.1", "2026", "STU-002", "", "", "Central", "Kampala", "Nakasero", "A+",
        "0700000001",
    ])
    return response


@accountant_required
def bulk_students_errors_csv(request):
    """Download the error report from session."""
    errors = request.session.get("bulk_students_errors") or []
    if not errors:
        messages.info(request, "No error report available.")
        return redirect("portal:bulk_students_upload")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="students-errors.csv"'
    writer = csv.writer(response)

    headers = ["row"] + OPTIONAL_COLUMNS + REQUIRED_COLUMNS + ["errors"]
    writer.writerow(headers)

    for r in errors:
        line = [r.get("_line", "")]
        for col in OPTIONAL_COLUMNS + REQUIRED_COLUMNS:
            line.append(r.get(col, ""))
        line.append("; ".join(r.get("_errors", [])))
        writer.writerow(line)

    return response



# ---------- v0.9.2: Bulk marks entry ----------

from .decorators import teacher_required, current_teacher


@teacher_required
def bulk_marks_select(request):
    """List teacher's allocations with a 'Enter bulk marks' button."""
    teacher = current_teacher(request)
    school = current_school(request)

    if teacher is None:
        messages.error(request, "No teacher profile linked to your account.")
        return redirect("portal:teacher_home")

    allocations = (
        AllocatedSubject.objects
        .filter(teacher_name=teacher, school=school)
        .select_related("subject", "class_room", "class_room__name",
                        "class_room__stream", "term", "academic_year")
        .order_by("class_room__name__name", "class_room__stream__name", "subject__name")
    )

    return render(request, "portal/bulk_marks_select.html", {
        "teacher": teacher,
        "allocations": allocations,
    })


@teacher_required
def bulk_marks_entry(request, allocation_id):
    """Enter marks for every student in a class in one table."""
    allocation = get_object_or_404(AllocatedSubject, pk=allocation_id)
    teacher = current_teacher(request)

    if allocation.teacher_name_id != teacher.id and not request.user.is_superuser:
        messages.error(request, "You are not assigned to this subject.")
        return redirect("portal:bulk_marks_select")

    # Determine the term
    term = allocation.term or (
        Term.objects.filter(academic_year=allocation.academic_year)
        .order_by("-start_date")
        .first()
    )
    if term is None:
        messages.error(request, "No term found for this allocation.")
        return redirect("portal:bulk_marks_select")

    # Exams for this class + term
    exams = (
        ExaminationListHandler.objects
        .filter(school=allocation.school, term=term, classrooms=allocation.class_room)
        .order_by("name")
    )

    # Students enrolled
    enrollments = (
        StudentClassEnrollment.objects
        .filter(
            classroom=allocation.class_room,
            academic_year=allocation.academic_year,
            student__isnull=False,
        )
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )

    # Exam selection
    exam_id = request.POST.get("exam_id") or request.GET.get("exam_id")
    selected_exam = exams.filter(pk=exam_id).first() if exam_id else exams.first()

    saved = 0
    errors_list = []
    warnings_list = []

    if request.method == "POST" and selected_exam:
        for enrollment in enrollments:
            field_name = f"score_{enrollment.pk}"
            raw = request.POST.get(field_name, "").strip()

            # Empty = leave unchanged
            if raw == "":
                continue

            try:
                score = float(raw)
            except ValueError:
                errors_list.append(f"{enrollment.student.full_name}: '{raw}' is not a number.")
                continue

            if score < 0 or score > selected_exam.out_of:
                errors_list.append(
                    f"{enrollment.student.full_name}: {score} is outside 0–{selected_exam.out_of}."
                )
                continue

            # Lock check
            existing = MarksManagement.objects.filter(
                school=allocation.school,
                exam_name=selected_exam,
                subject=allocation.subject,
                student=enrollment,
            ).first()

            if existing and existing._submission_is_locked():
                warnings_list.append(
                    f"{enrollment.student.full_name}: submission is locked — skipped."
                )
                continue

            try:
                if existing:
                    existing.points_scored = score
                    existing.created_by = teacher
                    existing.save()
                else:
                    MarksManagement.objects.create(
                        school=allocation.school,
                        exam_name=selected_exam,
                        subject=allocation.subject,
                        student=enrollment,
                        points_scored=score,
                        created_by=teacher,
                    )
                saved += 1
            except Exception as e:
                errors_list.append(f"{enrollment.student.full_name}: {e}")

        if saved:
            messages.success(request, f"Saved {saved} marks.")
        if warnings_list:
            messages.warning(request, " ".join(warnings_list[:5]))
        if errors_list:
            messages.error(request, " ".join(errors_list[:5]))

        return redirect(
            f"/portal/teacher/bulk-marks/{allocation.id}/?exam_id={selected_exam.id}"
        )

    # Build table rows with existing scores
    existing_map = {}
    if selected_exam:
        for m in MarksManagement.objects.filter(
            exam_name=selected_exam,
            subject=allocation.subject,
            student__in=enrollments,
        ):
            existing_map[m.student_id] = m.points_scored

    rows = []
    for e in enrollments:
        rows.append({
            "enrollment": e,
            "student": e.student,
            "score": existing_map.get(e.pk, ""),
        })

    return render(request, "portal/bulk_marks_entry.html", {
        "allocation": allocation,
        "term": term,
        "exams": exams,
        "selected_exam": selected_exam,
        "rows": rows,
        "out_of": selected_exam.out_of if selected_exam else None,
    })



# ---------- v0.9.5: Bulk receipt printing ----------

from datetime import date, timedelta
from django.utils.dateparse import parse_date


def _accountant_or_staff(request):
    u = request.user
    return bool(u.is_staff or u.is_superuser or getattr(u, "is_accountant", False))


@accountant_required
def bulk_receipts_picker(request):
    """Pick a date range and optional student filter."""
    if not _accountant_or_staff(request):
        messages.error(request, "Accountant access required.")
        return redirect("portal:accountant_home")

    school = current_school(request)
    if school is None and not request.user.is_superuser:
        messages.error(request, "No school linked to your account.")
        return redirect("portal:accountant_home")

    schools = None
    if school is None:
        from administration.models import School
        schools = School.objects.all().order_by("name")
        chosen_id = request.GET.get("school")
        if chosen_id:
            school = schools.filter(pk=chosen_id).first()

    from academic.models import Student
    students = Student.objects.none()
    if school is not None:
        students = (
            Student.objects
            .filter(school=school)
            .order_by("last_name", "first_name")
        )

    today = date.today()
    default_from = today - timedelta(days=30)

    return render(request, "portal/bulk_receipts_picker.html", {
        "school": school,
        "schools": schools,
        "students": students,
        "default_from": default_from.isoformat(),
        "default_to": today.isoformat(),
    })


@accountant_required
def bulk_receipts_view(request):
    """Render all matching receipts stacked for browser print."""
    if not _accountant_or_staff(request):
        messages.error(request, "Accountant access required.")
        return redirect("portal:accountant_home")

    school = current_school(request)
    school_id = request.GET.get("school")
    if school is None and request.user.is_superuser and school_id:
        from administration.models import School
        school = School.objects.filter(pk=school_id).first()
    if school is None:
        messages.error(request, "Pick a school first.")
        return redirect("portal:bulk_receipts_picker")

    from finance.models import Receipt

    qs = (
        Receipt.objects
        .filter(school=school)
        .select_related("student", "paid_for", "received_by")
        .order_by("payment_date", "id")
    )

    date_from = parse_date(request.GET.get("from") or "")
    date_to = parse_date(request.GET.get("to") or "")
    student_id = request.GET.get("student")

    if date_from:
        qs = qs.filter(payment_date__gte=date_from)
    if date_to:
        qs = qs.filter(payment_date__lte=date_to)
    if student_id:
        qs = qs.filter(student_id=student_id)

    receipts = list(qs[:500])

    total = sum((r.amount or 0) for r in receipts)

    return render(request, "portal/bulk_receipts_view.html", {
        "school": school,
        "receipts": receipts,
        "date_from": date_from,
        "date_to": date_to,
        "total": total,
        "generated_at": timezone.now(),
    })