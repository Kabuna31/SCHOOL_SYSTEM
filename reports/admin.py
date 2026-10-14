from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.utils.html import format_html

from academic.models import ClassRoom, Student, StudentClassEnrollment
from administration.models import School, Term


class ReportsAdminSite:
    """Not a real model admin — just a placeholder for the sidebar."""


# Custom admin view that appears in the sidebar
from django.contrib.admin import AdminSite


def reports_dashboard(request):
    user = request.user
    school = getattr(user, "school", None) or School.objects.filter(active=True).first()

    terms = Term.objects.filter(academic_year__school=school).order_by("-start_date") if school else []
    classrooms = ClassRoom.objects.filter(school=school).order_by("name__name", "stream__name") if school else []

    context = {
        **admin.site.each_context(request),
        "title": "Reports",
        "school": school,
        "terms": terms,
        "classrooms": classrooms,
    }
    return render(request, "reports/home.html", context)

_original_get_urls = admin.site.get_urls

def get_urls_with_reports():
    urls = _original_get_urls()
    custom = [
        path("reports/", admin.site.admin_view(reports_dashboard), name="reports_dashboard"),
    ]
    return custom + urls

admin.site.get_urls = get_urls_with_reports