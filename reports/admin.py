from django.contrib import admin

from .models import ReportCard


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = (
        "student_display",
        "term",
        "general_grade",
        "position_display_admin",
        "attendance_display",
        "school",
    )
    list_filter = ("school", "term__academic_year", "term")
    search_fields = (
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("student",)
    fieldsets = (
        ("Identity", {"fields": ("school", "student", "term")}),
        ("Comments", {"fields": ("class_teacher_comment", "general_comment", "head_teacher_comment")}),
        ("Grades & Points", {"fields": ("general_grade", "points_scored")}),
        ("Position", {"fields": ("position_in_class", "out_of_class")}),
        ("Attendance", {"fields": ("days_present", "days_absent")}),
        ("Dates", {"fields": ("term_ended_on", "next_term_begins_on")}),
        ("Audit", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def student_display(self, obj):
        return f"{obj.student.admission_number} — {obj.student.full_name}"
    student_display.short_description = "Student"

    def position_display_admin(self, obj):
        return obj.position_display or "—"
    position_display_admin.short_description = "Position"

    def attendance_display(self, obj):
        return obj.attendance_summary or "—"
    attendance_display.short_description = "Attendance"