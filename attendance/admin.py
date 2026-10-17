from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import (
    AttendanceStatus,
    TeachersAttendance,
    StudentAttendance,
    PeriodAttendance,
)
from .resources import StudentAttendanceResource
from school.admin_utils import enable_import_export


# Simple models — default resource is fine
enable_import_export(AttendanceStatus)
enable_import_export(TeachersAttendance)
enable_import_export(PeriodAttendance)


# StudentAttendance — custom resource with readable student name
@admin.register(StudentAttendance)
class StudentAttendanceAdmin(ImportExportModelAdmin):
    resource_class = StudentAttendanceResource
    change_list_template = "admin/import_export/change_list_import_export.html"
    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )