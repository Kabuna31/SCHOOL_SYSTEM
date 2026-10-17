from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from .models import Receipt, Payment, DebtRecord, ReceiptAllocation
from academic.models import Student


class ReceiptResource(resources.ModelResource):
    student = fields.Field(
        column_name="student",
        attribute="student",
        widget=ForeignKeyWidget(Student, "admission_number"),
    )
    paid_for = fields.Field(
        column_name="paid_for",
        attribute="paid_for",
        widget=ForeignKeyWidget(ReceiptAllocation, "name"),
    )

    class Meta:
        model = Receipt
        fields = (
            "receipt_number",
            "student",
            "payer",
            "amount",
            "payment_date",
            "paid_through",
            "paid_for",
            "status",
        )
        export_order = fields
        import_id_fields = ("receipt_number",)
        exclude = ("id", "school", "received_by", "created_at")
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")


class PaymentResource(resources.ModelResource):
    class Meta:
        model = Payment
        fields = ("reference", "amount", "payment_date", "method", "status")
        export_order = fields
        import_id_fields = ("reference",)
        exclude = ("id", "school", "recorded_by")
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")


class DebtRecordResource(resources.ModelResource):
    student = fields.Field(
        column_name="student",
        attribute="student",
        widget=ForeignKeyWidget(Student, "admission_number"),
    )

    class Meta:
        model = DebtRecord
        fields = ("student", "term", "amount_added", "amount_paid", "is_reversed")
        export_order = fields
        import_id_fields = ("student", "term")
        exclude = ("id", "school", "created_at", "updated_at")
        export_formats = ("csv", "xlsx")
        import_formats = ("csv", "xlsx")