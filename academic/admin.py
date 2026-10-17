from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

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


# ---------- Student (custom admin with search_fields for autocomplete) ----------
@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource
    change_list_template = "admin/import_export/change_list_import_export.html"
    search_fields = (
        "admission_number",
        "first_name",
        "middle_name",
        "last_name",
        "parent_contact",
    )


# ---------- Other models with custom resource ----------
@admin.register(Subject)
class SubjectAdmin(ImportExportModelAdmin):
    resource_class = SubjectResource
    change_list_template = "admin/import_export/change_list_import_export.html"
    search_fields = ("name",)


@admin.register(Teacher)
class TeacherAdmin(ImportExportModelAdmin):
    resource_class = TeacherResource
    change_list_template = "admin/import_export/change_list_import_export.html"
    search_fields = ("first_name", "last_name", "email")


@admin.register(Parent)
class ParentAdmin(ImportExportModelAdmin):
    resource_class = ParentResource
    change_list_template = "admin/import_export/change_list_import_export.html"
    search_fields = ("first_name", "last_name", "email")


@admin.register(ClassLevel)
class ClassLevelAdmin(ImportExportModelAdmin):
    resource_class = ClassLevelResource
    change_list_template = "admin/import_export/change_list_import_export.html"
    search_fields = ("name",)


@admin.register(ClassYear)
class ClassYearAdmin(ImportExportModelAdmin):
    resource_class = ClassYearResource
    change_list_template = "admin/import_export/change_list_import_export.html"
    search_fields = ("year",)


@admin.register(Stream)
class StreamAdmin(ImportExportModelAdmin):
    resource_class = StreamResource
    change_list_template = "admin/import_export/change_list_import_export.html"
    search_fields = ("name",)


@admin.register(ClassRoom)
class ClassRoomAdmin(ImportExportModelAdmin):
    resource_class = ClassRoomResource
    change_list_template = "admin/import_export/change_list_import_export.html"
    search_fields = ("name__name", "stream__name")


@admin.register(StudentClassEnrollment)
class StudentClassEnrollmentAdmin(ImportExportModelAdmin):
    resource_class = StudentClassEnrollmentResource
    change_list_template = "admin/import_export/change_list_import_export.html"
    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )


@admin.register(AllocatedSubject)
class AllocatedSubjectAdmin(ImportExportModelAdmin):
    resource_class = AllocatedSubjectResource
    change_list_template = "admin/import_export/change_list_import_export.html"
    search_fields = ("teacher_name__first_name", "teacher_name__last_name", "subject__name")


# ---------- Simple models (default import/export) ----------
enable_import_export(Department)
enable_import_export(GradeLevel)
enable_import_export(Topic)
enable_import_export(SubTopic)
enable_import_export(Dormitory)
enable_import_export(DormitoryAllocation)
enable_import_export(MessageToParent)
enable_import_export(MessageToTeacher)