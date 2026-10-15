from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def teacher_required(view_func):
    @wraps(view_func)
    @login_required(login_url="/portal/login/")
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.is_teacher:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Teacher access required.")
    return wrapper


def accountant_required(view_func):
    @wraps(view_func)
    @login_required(login_url="/portal/login/")
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.is_accountant:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Accountant access required.")
    return wrapper


def parent_required(view_func):
    @wraps(view_func)
    @login_required(login_url="/portal/login/")
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.is_parent:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Parent access required.")
    return wrapper


def current_teacher(request):
    """Return the Teacher object for the logged-in user, or None."""
    user = request.user
    if hasattr(user, "academic_teacher"):
        return user.academic_teacher
    return None


def current_school(request):
    user = request.user
    if hasattr(user, "school") and user.school:
        return user.school
    return None


def portal_redirect(user):
    """Send a logged-in user to the right portal home page."""
    if user.is_superuser or user.is_staff:
        return "/admin/"
    if user.is_teacher:
        return "/portal/teacher/"
    if user.is_accountant:
        return "/portal/accountant/"
    if user.is_parent:
        return "/portal/parent/"
    return "/portal/login/"