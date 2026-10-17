from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.shortcuts import render


admin.site.site_header = "School Management System Administration"
admin.site.site_title = "School Admin Portal"
admin.site.index_title = "Welcome to the School Management Dashboard"


def api_welcome(request):
    return JsonResponse({
        "message": "Welcome to the School Management System API",
        "admin_panel": "/admin/",
    })


def _wants_json(request):
    return request.path.startswith("/api/")


def custom_404_handler(request, exception=None):
    if _wants_json(request):
        return JsonResponse(
            {"error": "Page Not Found", "detail": str(exception) or "Not found"},
            status=404,
        )
    return render(request, "404.html", status=404)


def custom_500_handler(request):
    if _wants_json(request):
        return JsonResponse(
            {"error": "Server Error", "detail": "An unexpected error occurred."},
            status=500,
        )
    return render(request, "500.html", status=500)


def custom_403_handler(request, exception=None):
    if _wants_json(request):
        return JsonResponse(
            {"error": "Permission Denied", "detail": str(exception) or "Forbidden"},
            status=403,
        )
    return render(request, "403.html", status=403)


def custom_400_handler(request, exception=None):
    if _wants_json(request):
        return JsonResponse(
            {"error": "Bad Request", "detail": str(exception) or "Bad request"},
            status=400,
        )
    return render(request, "400.html", status=400)


def _debug_csrf(request):
    import os
    from django.conf import settings as s
    return JsonResponse({
        "CSRF_TRUSTED_ORIGINS": s.CSRF_TRUSTED_ORIGINS,
        "ALLOWED_HOSTS": s.ALLOWED_HOSTS,
        "RENDER_EXTERNAL_HOSTNAME": os.environ.get("RENDER_EXTERNAL_HOSTNAME", "NOT SET"),
        "CSRF_COOKIE_SECURE": s.CSRF_COOKIE_SECURE,
        "SESSION_COOKIE_SECURE": s.SESSION_COOKIE_SECURE,
        "CSRF_COOKIE_SAMESITE": s.CSRF_COOKIE_SAMESITE,
        "SESSION_COOKIE_SAMESITE": s.SESSION_COOKIE_SAMESITE,
        "SESSION_COOKIE_DOMAIN": getattr(s, "SESSION_COOKIE_DOMAIN", None),
        "CSRF_COOKIE_DOMAIN": getattr(s, "CSRF_COOKIE_DOMAIN", None),
        "SESSION_COOKIE_NAME": s.SESSION_COOKIE_NAME,
        "CSRF_COOKIE_NAME": s.CSRF_COOKIE_NAME,
        "DEBUG": s.DEBUG,
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", api_welcome),
    path("api/academic/", include("api.academic.urls")),
    path("api/administration/", include("api.administration.urls")),
    path("api/attendance/", include("api.attendance.urls")),
    path("api/notifications/", include("automation.urls")),
    path("api/assignments/", include("api.assignments.urls")),
    path("api/blog/", include("api.blog.urls")),
    path("api/examination/", include("api.examination.urls")),
    path("api/finance/", include("api.finance.urls")),
    path("api/users/", include("api.users.urls")),
    path("api/timetable/", include("api.schedule.urls")),
    path("api/sis/", include("api.sis.urls")),
    path("reports/", include("reports.urls")),
    path("portal/", include("portal.urls")),
    path("__debug_csrf/", _debug_csrf),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = custom_404_handler
handler500 = custom_500_handler
handler403 = custom_403_handler
handler400 = custom_400_handler