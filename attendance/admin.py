from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from academic.models import Student, StudentClassEnrollment, ClassRoom
from .models import (
    AttendanceStatus,
    TeachersAttendance,
    StudentAttendance,
    PeriodAttendance,
)
from school.admin_utils import enable_import_export


# Simple models — no custom resource needed
enable_import_export(AttendanceStatus)
enable_import_export(TeachersAttendance)
enable_import_export(PeriodAttendance)


# StudentAttendance — custom resource
class StudentAttendanceResource(resources.ModelResource):
    student = fields.Field(
        column_name="student",
        attribute="student",
        widget=ForeignKeyWidget(Student, field="admission_number"),
    )
    status = fields.Field(
        column_name="status",
        attribute="status",
        widget=ForeignKeyWidget(AttendanceStatus, field="name"),
    )

    class Meta:
        model = StudentAttendance
        fields = ("student", "date", "status")
        import_id_fields = ("student", "date")
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")


admin.site.register(StudentAttendance, ImportExportModelAdmin)  # ← replace existing registration