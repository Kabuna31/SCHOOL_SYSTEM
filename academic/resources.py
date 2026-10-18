from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from .models import (
    Student,
    Subject,
    Teacher,
    Parent,
    ClassLevel,
    ClassYear,
    Stream,
    ClassRoom,
    StudentClassEnrollment,
    AllocatedSubject,
    School,
)


class StudentResource(resources.ModelResource):
    class_level = fields.Field(
        column_name="class_level",
        attribute="class_level",
        widget=ForeignKeyWidget(ClassLevel, "name"),
    )
    class_of_year = fields.Field(
        column_name="class_of_year",
        attribute="class_of_year",
        widget=ForeignKeyWidget(ClassYear, "year"),
    )

    class Meta:
        model = Student
        fields = (
            "admission_number",
            "first_name",
            "middle_name",
            "last_name",
            "gender",
            "date_of_birth",
            "parent_contact",
            "region",
            "city",
            "street",
            "blood_group",
            "class_level",
            "class_of_year",
        )
        export_order = fields
        import_id_fields = ("admission_number",)
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")


class SubjectResource(resources.ModelResource):
    class Meta:
        model = Subject
        fields = ("name",)
        export_order = fields
        import_id_fields = ("name",)


class TeacherResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )

    class Meta:
        model = Teacher
        fields = (
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "phone_number",
            "gender",
            "school",
        )
        export_order = fields
        import_id_fields = ("email",)


class ParentResource(resources.ModelResource):
    class Meta:
        model = Parent
        fields = ("first_name", "last_name", "email", "phone_number")
        export_order = fields
        import_id_fields = ("email",)


class ClassLevelResource(resources.ModelResource):
    class Meta:
        model = ClassLevel
        fields = ("name",)
        export_order = fields
        import_id_fields = ("name",)


class ClassYearResource(resources.ModelResource):
    class Meta:
        model = ClassYear
        fields = ("year", "full_name")
        export_order = fields
        import_id_fields = ("year",)


class StreamResource(resources.ModelResource):
    class Meta:
        model = Stream
        fields = ("name",)
        export_order = fields
        import_id_fields = ("name",)


class ClassRoomResource(resources.ModelResource):
    class_level = fields.Field(
        column_name="class_level",
        attribute="name",
        widget=ForeignKeyWidget(ClassLevel, "name"),
    )
    stream = fields.Field(
        column_name="stream",
        attribute="stream",
        widget=ForeignKeyWidget(Stream, "name"),
    )

    class Meta:
        model = ClassRoom
        fields = ("class_level", "stream", "capacity")
        export_order = fields


class StudentClassEnrollmentResource(resources.ModelResource):
    student = fields.Field(
        column_name="student",
        attribute="student",
        widget=ForeignKeyWidget(Student, "admission_number"),
    )

    class Meta:
        model = StudentClassEnrollment
        fields = ("student", "academic_year", "classroom")
        export_order = fields


class AllocatedSubjectResource(resources.ModelResource):
    teacher = fields.Field(
        column_name="teacher",
        attribute="teacher_name",
        widget=ForeignKeyWidget(Teacher, "email"),
    )
    subject = fields.Field(
        column_name="subject",
        attribute="subject",
        widget=ForeignKeyWidget(Subject, "name"),
    )

    class Meta:
        model = AllocatedSubject
        fields = ("teacher", "subject", "class_room")
        export_order = fields