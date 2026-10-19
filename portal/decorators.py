def portal_redirect(user):
    """Send a logged-in user to the right portal home page.

    Never returns /admin/ — superusers use /admin/login/ directly.
    """
    if getattr(user, "is_teacher", False):
        return "/portal/teacher/"
    if getattr(user, "is_parent", False):
        return "/portal/parent/"
    if getattr(user, "is_student", False):
        return "/portal/student/"
    # fallback for anyone else — never admin
    return "/portal/"