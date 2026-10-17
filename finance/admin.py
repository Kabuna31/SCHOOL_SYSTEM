from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget

from academic.models import Student, StudentClassEnrollment
from administration.models import Term
from users.models import CustomUser
from .models import (
    ReceiptAllocation,
    Receipt,
    PaymentAllocation,
    Payment,
)
from school.admin_utils import enable_import_export


# ---------- Payment ----------
class PaymentResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(
            Payment._meta.get_field("school").related_model, field="name"
        ),
    )
    paid_for = fields.Field(
        column_name="paid_for",
        attribute="paid_for",
        widget=ForeignKeyWidget(PaymentAllocation, field="name"),
    )
    paid_by = fields.Field(
        column_name="paid_by",
        attribute="paid_by",
        widget=ForeignKeyWidget(CustomUser, field="email"),
    )

    class Meta:
        model = Payment
        import_id_fields = ("payment_number",)
        fields = (
            "payment_number",
            "date",
            "school",
            "paid_to",
            "paid_for",
            "paid_through",
            "amount",
            "status",
            "paid_by",
        )
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")


@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    resource_class = PaymentResource
    change_list_template = "admin/import_export/change_list_import_export.html"


# ---------- Receipt ----------
class ReceiptResource(resources.ModelResource):
    school = fields.Field(
        column_name="school",
        attribute="school",
        widget=ForeignKeyWidget(
            Receipt._meta.get_field("school").related_model, field="name"
        ),
    )
    student = fields.Field(
        column_name="student",
        attribute="student",
        widget=ForeignKeyWidget(Student, field="admission_number"),
    )
    paid_for = fields.Field(
        column_name="paid_for",
        attribute="paid_for",
        widget=ForeignKeyWidget(ReceiptAllocation, field="name"),
    )
    received_by = fields.Field(
        column_name="received_by",
        attribute="received_by",
        widget=ForeignKeyWidget(CustomUser, field="email"),
    )
    term = fields.Field(
        column_name="term",
        attribute="term",
        widget=ForeignKeyWidget(Term, field="name"),
    )

    class Meta:
        model = Receipt
        import_id_fields = ("receipt_number",)
        fields = (
            "receipt_number",
            "date",
            "payment_date",
            "school",
            "payer",
            "paid_for",
            "student",
            "amount",
            "paid_through",
            "term",
            "status",
            "received_by",
        )
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")


@admin.register(Receipt)
class ReceiptAdmin(ImportExportModelAdmin):
    resource_class = ReceiptResource
    change_list_template = "admin/import_export/change_list_import_export.html"


# ---------- Allocations ----------
enable_import_export(PaymentAllocation)
enable_import_export(ReceiptAllocation)