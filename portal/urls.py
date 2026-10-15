from django.urls import path
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
]