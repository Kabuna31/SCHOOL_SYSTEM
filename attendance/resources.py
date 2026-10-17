from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from .models import StudentAttendance
from academic.models import Student


class StudentAttendanceResource(resources.ModelResource):
    student = fields.Field(
        column_name="student",
        attribute="student",
        widget=ForeignKeyWidget(Student, "admission_number"),
    )

    class Meta:
        model = StudentAttendance
        fields = ("student", "date", "status")
        export_order = fields
        exclude = ("id", "school", "created_at", "updated_at")
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")