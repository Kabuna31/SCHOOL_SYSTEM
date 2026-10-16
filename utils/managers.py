from django.db import models
from utils.middleware import get_current_request

ObjectTypeQuerySet = models.QuerySet

class SchoolScopedManager(models.Manager):
    """
    Manager that automatically restricts queries to the logged-in user's school.
    Superusers bypass this restriction to see all schools.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        request = get_current_request()
        
        # If no request (e.g. management commands or migrations), return full queryset
        if not request or not hasattr(request, 'user'):
            return qs
            
        user = request.user
        
        # Unauthenticated users see nothing
        if not user.is_authenticated:
            return qs.none()
            
        # Superusers can view data across all schools
        if user.is_superuser:
            return qs
            
        # Filter by user's assigned school if present
        if hasattr(user, 'school') and user.school:
            return qs.filter(school=user.school)
            
        # Fallback: if user has no school assigned, return empty queryset for security
        return qs.none()



from django.db import models
from administration.managers import SchoolScopedManager

class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    school = models.ForeignKey('administration.School', on_delete=models.CASCADE)
    
    # Use the school-scoped manager as the default manager
    objects = SchoolScopedManager()
    
    # Keep an unfiltered manager available if you ever need raw system-wide access
    unfiltered_objects = models.Manager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"