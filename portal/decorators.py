from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def teacher_required(view_func):
    @wraps(view_func)
    @login_required(login_url="/login/")
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.is_teacher:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Teacher access required.")
    return wrapper


def accountant_required(view_func):
    @wraps(view_func)
    @login_required(login_url="/login/")
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.is_accountant:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied("Accountant access required.")
    return wrapper


def parent_required(view_func):
    @wraps(view_func)
    @login_required(login_url="/login/")
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
    """Send a logged-in user to the right portal home page.

    Never returns /admin/ — the admin login is separate at /admin/login/.
    """
    if user.is_teacher:
        return "/portal/teacher/"
    if user.is_accountant:
        return "/portal/accountant/"
    if user.is_parent:
        return "/portal/parent/"
    # Fallback for superusers and anyone without a specific portal role.
    # Superusers can still reach /admin/ manually, but the portal login
    # always lands on the portal.
    return "/portal/"


def current_school_required(view_func):
    """Ensure the logged-in user is bound to a school."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if current_school(request) is None:
            raise PermissionDenied("Your account is not associated with a school.")
        return view_func(request, *args, **kwargs)
    return wrapper