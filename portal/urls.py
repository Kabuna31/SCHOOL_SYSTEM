from django.urls import path
from . import bulk_views as views_bulk
from . import views

app_name = "portal"

urlpatterns = [
    path("login/", views.portal_login, name="login"),
    path("logout/", views.portal_logout, name="logout"),

    path("teacher/", views.teacher_home, name="teacher_home"),
    path("teacher/marks/<int:allocation_id>/", views.teacher_marks_entry, name="teacher_marks_entry"),
    path("teacher/attendance/<int:allocation_id>/", views.teacher_attendance, name="teacher_attendance"),

    path("accountant/", views.accountant_home, name="accountant_home"),
    path("parent/", views.parent_home, name="parent_home"),

    path("accountant/payment/add/", views.accountant_payment_add, name="accountant_payment_add"),
    path("accountant/receipts/", views.accountant_receipts, name="accountant_receipts"),

    path("parent/child/<int:student_id>/", views.parent_child_detail, name="parent_child_detail"),

    # Bulk student import (v0.9.1)
    path("admin/bulk-students/", views_bulk.bulk_students_upload, name="bulk_students_upload"),
    path("admin/bulk-students/confirm/", views_bulk.bulk_students_confirm, name="bulk_students_confirm"),
    path("admin/bulk-students/sample/", views_bulk.bulk_students_sample, name="bulk_students_sample"),
    path("admin/bulk-students/errors.csv", views_bulk.bulk_students_errors_csv, name="bulk_students_errors_csv"),
]