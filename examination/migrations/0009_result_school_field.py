import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("examination", "0008_seed_grade_scales"),
        ("administration", "0003_school_class_teacher_signature_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="result",
                    name="school",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="administration.school",
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]