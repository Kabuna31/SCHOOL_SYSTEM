from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.reports_home, name="home"),
    path(
        "report-card/<int:student_id>/<int:term_id>/",
        views.report_card,
        name="report_card",
    ),
    path(
        "report-card/<int:student_id>/<int:term_id>/print/",
        views.report_card_print,
        name="report_card_print",
    ),
    path("bulk/<int:classroom_id>/<int:term_id>/", views.bulk_report_cards, name="bulk"),
]