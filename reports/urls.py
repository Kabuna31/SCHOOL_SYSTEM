from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.reports_home, name="home"),

    path("report-card-picker/", views.report_card_picker, name="report_card_picker"),
    path("report-card/<int:student_id>/<int:term_id>/", views.report_card, name="report_card"),

    path("marksheet-picker/", views.marksheet_picker, name="marksheet_picker"),
    path("marksheet/<int:classroom_id>/<int:term_id>/", views.marksheet, name="marksheet"),

    path("analysis-picker/", views.analysis_picker, name="analysis_picker"),
    path("analysis/<int:classroom_id>/<int:term_id>/", views.analysis, name="analysis"),

    path("generate/<int:classroom_id>/<int:term_id>/", views.generate_for_class, name="generate_for_class"),
    path("fee-statement/<int:student_id>/", views.fee_statement, name="fee_statement"),
    path("defaulters/", views.defaulters, name="defaulters"),
    path("class-marks/<int:classroom_id>/<int:term_id>/", views.class_marks_record, name="class_marks_record"),
]