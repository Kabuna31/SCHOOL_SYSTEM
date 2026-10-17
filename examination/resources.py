from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from .models import MarksManagement, ExaminationListHandler
from academic.models import StudentClassEnrollment, Subject, Teacher


class MarksManagementResource(resources.ModelResource):
    student = fields.Field(
        column_name="student",
        attribute="student",
        widget=ForeignKeyWidget(StudentClassEnrollment, "student__admission_number"),
    )
    subject = fields.Field(
        column_name="subject",
        attribute="subject",
        widget=ForeignKeyWidget(Subject, "name"),
    )
    exam_name = fields.Field(
        column_name="exam_name",
        attribute="exam_name",
        widget=ForeignKeyWidget(ExaminationListHandler, "name"),
    )
    teacher = fields.Field(
        column_name="teacher",
        attribute="created_by",
        widget=ForeignKeyWidget(Teacher, "email"),
    )

    class Meta:
        model = MarksManagement
        fields = (
            "student",
            "exam_name",
            "subject",
            "points_scored",
            "teacher",
        )
        export_order = fields
        exclude = ("id", "school", "date_time")
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")


class ExaminationListHandlerResource(resources.ModelResource):
    class Meta:
        model = ExaminationListHandler
        fields = (
            "name",
            "assessment_type",
            "start_date",
            "ends_date",
            "out_of",
        )
        export_order = fields
        import_id_fields = ("name",)
        exclude = ("id", "school", "term", "classrooms", "created_by", "created_on")
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")