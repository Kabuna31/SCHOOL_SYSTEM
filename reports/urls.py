from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
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
    path("dashboard/", views.dashboard, name="dashboard"),
    path("defaulters/send-sms/", views.send_defaulters_sms, name="send_defaulters_sms"),
    # Password reset
    path(
        "accounts/password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            success_url=reverse_lazy("password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "accounts/password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "accounts/password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]