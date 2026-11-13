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
    Department,
    GradeLevel,
    Topic,
    SubTopic,
    Dormitory,
    DormitoryAllocation,
    MessageToParent,
    MessageToTeacher,
)


class StudentResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )
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
            "id",
            "school",
            "admission_number",
            "first_name",
            "middle_name",
            "last_name",
            "gender",
            "religion",
            "date_of_birth",
            "graduation_date",
            "class_level",
            "class_of_year",
            "parent_contact",
            "parent_guardian",
            "region",
            "city",
            "street",
            "blood_group",
            "prems_number",
            "std_vii_number",
        )
        export_order = (
            "school",
            "admission_number",
            "first_name",
            "middle_name",
            "last_name",
            "gender",
            "religion",
            "date_of_birth",
            "graduation_date",
            "class_level",
            "class_of_year",
            "parent_contact",
            "parent_guardian",
            "region",
            "city",
            "street",
            "blood_group",
            "prems_number",
            "std_vii_number",
        )
        import_id_fields = ("admission_number",)


class SubjectResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )

    class Meta:
        model = Subject
        fields = ("id", "school", "name")
        export_order = ("school", "name")
        import_id_fields = ("school", "name")


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
            "school",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "phone_number",
            "gender",
            "date_of_birth",
        )
        export_order = (
            "school",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "phone_number",
            "gender",
            "date_of_birth",
        )
        import_id_fields = ("email",)


class ParentResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )

    class Meta:
        model = Parent
        fields = (
            "id",
            "school",
            "first_name",
            "last_name",
            "email",
            "phone_number",
        )
        export_order = (
            "school",
            "first_name",
            "last_name",
            "email",
            "phone_number",
        )
        import_id_fields = ("email",)


class ClassLevelResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )

    class Meta:
        model = ClassLevel
        fields = ("id", "school", "name")
        export_order = ("school", "name")
        import_id_fields = ("school", "name")


class ClassYearResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )

    class Meta:
        model = ClassYear
        fields = ("id", "school", "year", "full_name")
        export_order = ("school", "year", "full_name")
        import_id_fields = ("school", "year")


class StreamResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )

    class Meta:
        model = Stream
        fields = ("id", "school", "name")
        export_order = ("school", "name")
        import_id_fields = ("school", "name")


class ClassRoomResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )
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
    class_teacher = fields.Field(
        column_name="class_teacher",
        attribute="class_teacher",
        widget=ForeignKeyWidget(Teacher, "user__email"),
    )

    class Meta:
        model = ClassRoom
        fields = (
            "id",
            "school",
            "class_level",
            "stream",
            "class_teacher",
            "capacity",
            "occupied_sits",
        )
        export_order = (
            "school",
            "class_level",
            "stream",
            "class_teacher",
            "capacity",
            "occupied_sits",
        )
        import_id_fields = ("school", "class_level", "stream")


class StudentClassEnrollmentResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )
    student = fields.Field(
        column_name="student",
        attribute="student",
        widget=ForeignKeyWidget(Student, "admission_number"),
    )
    classroom = fields.Field(
        column_name="classroom",
        attribute="classroom",
        widget=ForeignKeyWidget(ClassRoom, "id"),
    )

    class Meta:
        model = StudentClassEnrollment
        fields = (
            "id",
            "school",
            "student",
            "classroom",
            "academic_year",
        )
        export_order = (
            "school",
            "student",
            "classroom",
            "academic_year",
        )
        import_id_fields = ("student", "academic_year")


class AllocatedSubjectResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )
    teacher = fields.Field(
        column_name="teacher",
        attribute="teacher_name",
        widget=ForeignKeyWidget(Teacher, "user__email"),
    )
    subject = fields.Field(
        column_name="subject",
        attribute="subject",
        widget=ForeignKeyWidget(Subject, "name"),
    )

    class Meta:
        model = AllocatedSubject
        fields = (
            "id",
            "school",
            "teacher",
            "subject",
            "class_room",
            "term",
            "academic_year",
        )
        export_order = (
            "school",
            "teacher",
            "subject",
            "class_room",
            "term",
            "academic_year",
        )
        import_id_fields = ("teacher", "subject", "class_room", "term")


class DepartmentResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )

    class Meta:
        model = Department
        fields = ("id", "school", "name")
        export_order = ("school", "name")
        import_id_fields = ("school", "name")


class GradeLevelResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )

    class Meta:
        model = GradeLevel
        fields = ("id", "school", "name")
        export_order = ("school", "name")
        import_id_fields = ("school", "name")


class TopicResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )

    class Meta:
        model = Topic
        fields = ("id", "school", "name", "subject")
        export_order = ("school", "name", "subject")
        import_id_fields = ("school", "name")


class SubTopicResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )

    class Meta:
        model = SubTopic
        fields = ("id", "school", "name", "topic")
        export_order = ("school", "name", "topic")
        import_id_fields = ("school", "name")


class DormitoryResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )

    class Meta:
        model = Dormitory
        fields = ("id", "school", "name", "capacity", "occupied_beds")
        export_order = ("school", "name", "capacity", "occupied_beds")
        import_id_fields = ("school", "name")


class DormitoryAllocationResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )
    student = fields.Field(
        column_name="student",
        attribute="student",
        widget=ForeignKeyWidget(Student, "admission_number"),
    )

    class Meta:
        model = DormitoryAllocation
        fields = ("id", "school", "student", "dormitory")
        export_order = ("school", "student", "dormitory")
        import_id_fields = ("school", "student")


class MessageToParentResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )
    parent = fields.Field(
        column_name="parent",
        attribute="parent",
        widget=ForeignKeyWidget(Parent, "email"),
    )

    class Meta:
        model = MessageToParent
        fields = ("id", "school", "parent", "subject", "message", "sent_at")
        export_order = ("school", "parent", "subject", "message", "sent_at")
        import_id_fields = ("school", "parent", "sent_at")


class MessageToTeacherResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(School, "name"),
    )
    teacher = fields.Field(
        column_name="teacher",
        attribute="teacher",
        widget=ForeignKeyWidget(Teacher, "user__email"),
    )

    class Meta:
        model = MessageToTeacher
        fields = ("id", "school", "teacher", "subject", "message", "sent_at")
        export_order = ("school", "teacher", "subject", "message", "sent_at")
        import_id_fields = ("school", "teacher", "sent_at")