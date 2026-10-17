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


# Models with custom resource
class StudentAdmin(ImportExportModelAdmin):
    resource_class = StudentResource

class SubjectAdmin(ImportExportModelAdmin):
    resource_class = SubjectResource

class TeacherAdmin(ImportExportModelAdmin):
    resource_class = TeacherResource

class ParentAdmin(ImportExportModelAdmin):
    resource_class = ParentResource

class ClassLevelAdmin(ImportExportModelAdmin):
    resource_class = ClassLevelResource

class ClassYearAdmin(ImportExportModelAdmin):
    resource_class = ClassYearResource

class StreamAdmin(ImportExportModelAdmin):
    resource_class = StreamResource

class ClassRoomAdmin(ImportExportModelAdmin):
    resource_class = ClassRoomResource

class StudentClassEnrollmentAdmin(ImportExportModelAdmin):
    resource_class = StudentClassEnrollmentResource

class AllocatedSubjectAdmin(ImportExportModelAdmin):
    resource_class = AllocatedSubjectResource


# Register with custom resource
admin.site.register(Student, StudentAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Parent, ParentAdmin)
admin.site.register(ClassLevel, ClassLevelAdmin)
admin.site.register(ClassYear, ClassYearAdmin)
admin.site.register(Stream, StreamAdmin)
admin.site.register(ClassRoom, ClassRoomAdmin)
admin.site.register(StudentClassEnrollment, StudentClassEnrollmentAdmin)
admin.site.register(AllocatedSubject, AllocatedSubjectAdmin)


# Models using default enable_import_export (simple, no custom resource)
enable_import_export(Department)
enable_import_export(GradeLevel)
enable_import_export(Topic)
enable_import_export(SubTopic)
enable_import_export(Dormitory)
enable_import_export(DormitoryAllocation)
enable_import_export(MessageToParent)
enable_import_export(MessageToTeacher)