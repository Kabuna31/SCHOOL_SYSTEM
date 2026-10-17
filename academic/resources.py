from django.contrib import admin
from .models import *
from .resources import (
    StudentResource,
    SubjectResource,
    TeacherResource,
    ParentResource,
    ClassLevelResource,
    ClassYearResource,
    StreamResource,
    ClassRoomResource,
    StudentClassEnrollmentResource,
    AllocatedSubjectResource,
)
from school.admin_utils import enable_import_export


# Models with custom resource
enable_import_export(Student, resource_class=StudentResource)
enable_import_export(Subject, resource_class=SubjectResource)
enable_import_export(Teacher, resource_class=TeacherResource)
enable_import_export(Parent, resource_class=ParentResource)
enable_import_export(ClassLevel, resource_class=ClassLevelResource)
enable_import_export(ClassYear, resource_class=ClassYearResource)
enable_import_export(Stream, resource_class=StreamResource)
enable_import_export(ClassRoom, resource_class=ClassRoomResource)
enable_import_export(StudentClassEnrollment, resource_class=StudentClassEnrollmentResource)
enable_import_export(AllocatedSubject, resource_class=AllocatedSubjectResource)


# Models with default import/export (simple, no FK mess)
enable_import_export(Department)
enable_import_export(GradeLevel)
enable_import_export(Topic)
enable_import_export(SubTopic)
enable_import_export(Dormitory)
enable_import_export(DormitoryAllocation)
enable_import_export(MessageToParent)
enable_import_export(MessageToTeacher)

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
    class Meta:
        model = Teacher
        fields = (
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "phone_number",
            "gender",
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