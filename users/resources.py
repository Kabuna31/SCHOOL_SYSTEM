from import_export import resources

from .models import CustomUser, Accountant


class CustomUserResource(resources.ModelResource):
    class Meta:
        model = CustomUser
        fields = (
            "email",
            "first_name",
            "middle_name",
            "last_name",
            "phone_number",
            "is_teacher",
            "is_accountant",
            "is_parent",
            "is_staff",
            "is_active",
        )
        export_order = fields
        import_id_fields = ("email",)
        exclude = (
            "id",
            "password",
            "last_login",
            "date_joined",
            "is_superuser",
            "groups",
            "user_permissions",
            "school",
        )
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")

    def dehydrate_is_teacher(self, user):
        return "yes" if user.is_teacher else "no"

    def dehydrate_is_accountant(self, user):
        return "yes" if user.is_accountant else "no"

    def dehydrate_is_parent(self, user):
        return "yes" if user.is_parent else "no"

    def dehydrate_is_staff(self, user):
        return "yes" if user.is_staff else "no"

    def dehydrate_is_active(self, user):
        return "yes" if user.is_active else "no"


class AccountantResource(resources.ModelResource):
    class Meta:
        model = Accountant
        fields = ("first_name", "last_name", "email", "phone_number")
        export_order = fields
        import_id_fields = ("email",)
        exclude = ("id", "school", "user", "created_at", "updated_at")
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")