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
        # include id so re-imports from export don't fail
        fields = (
            "id",
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
        # don't export the internal id
        export_order = (
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
        import_id_fields = ("admission_number",)


class SubjectResource(resources.ModelResource):
    class Meta:
        model = Subject
        fields = ("id", "name")
        export_order = ("name",)
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
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "phone_number",
            "gender",
            "school",
        )
        export_order = (
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "phone_number",
            "gender",
            "school",
        )
        import_id_fields = ("email",)


class ParentResource(resources.ModelResource):
    class Meta:
        model = Parent
        fields = ("id", "first_name", "last_name", "email", "phone_number")
        export_order = ("first_name", "last_name", "email", "phone_number")
        import_id_fields = ("email",)


class ClassLevelResource(resources.ModelResource):
    class Meta:
        model = ClassLevel
        fields = ("id", "name")
        export_order = ("name",)
        import_id_fields = ("name",)


class ClassYearResource(resources.ModelResource):
    class Meta:
        model = ClassYear
        fields = ("id", "year", "full_name")
        export_order = ("year", "full_name")
        import_id_fields = ("year",)


class StreamResource(resources.ModelResource):
    class Meta:
        model = Stream
        fields = ("id", "name")
        export_order = ("name",)
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
        fields = ("id", "class_level", "stream", "capacity")
        export_order = ("class_level", "stream", "capacity")
        # use the natural combination to identify existing rooms
        import_id_fields = ("class_level", "stream")


class StudentClassEnrollmentResource(resources.ModelResource):
    student = fields.Field(
        column_name="student",
        attribute="student",
        widget=ForeignKeyWidget(Student, "admission_number"),
    )

    class Meta:
        model = StudentClassEnrollment
        fields = ("id", "student", "academic_year", "classroom")
        export_order = ("student", "academic_year", "classroom")
        import_id_fields = ("student", "academic_year")


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
        fields = ("id", "teacher", "subject", "class_room")
        export_order = ("teacher", "subject", "class_room")
        import_id_fields = ("teacher", "subject", "class_room")