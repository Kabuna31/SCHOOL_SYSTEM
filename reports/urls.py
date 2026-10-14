from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    # Hub
    path("", views.reports_home, name="home"),

    # Report Card picker + viewer
    path("report-card-picker/", views.report_card_picker, name="report_card_picker"),
    path("report-card/<int:student_id>/<int:term_id>/", views.report_card, name="report_card"),

    # Marksheet picker + viewer
    path("marksheet-picker/", views.marksheet_picker, name="marksheet_picker"),
    path("marksheet/<int:classroom_id>/<int:term_id>/", views.marksheet, name="marksheet"),

    # Analysis picker + viewer
    path("analysis-picker/", views.analysis_picker, name="analysis_picker"),
    path("analysis/<int:classroom_id>/<int:term_id>/", views.analysis, name="analysis"),

    # Bulk print
    path("bulk/<int:classroom_id>/<int:term_id>/", views.bulk_report_cards, name="bulk"),
]