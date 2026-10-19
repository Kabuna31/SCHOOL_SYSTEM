from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("examination", "0007_seed_grade_scales"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Drop the old GPA-style Result table entirely.
                migrations.RunSQL(
                    "DROP TABLE IF EXISTS examination_result CASCADE;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # Rename SubjectResult table to Result (preserves its data).
                migrations.RunSQL(
                    "ALTER TABLE examination_subjectresult RENAME TO examination_result;",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.DeleteModel(name="Result"),
                migrations.RenameModel(old_name="SubjectResult", new_name="Result"),
            ],
        ),
        # Rename constraint to match the new model name
        migrations.RemoveConstraint(
            model_name="result",
            name="unique_subject_result_scope",
        ),
        migrations.AddConstraint(
            model_name="result",
            constraint=models.UniqueConstraint(
                fields=("school", "student", "subject", "academic_year", "term"),
                name="unique_school_student_term_result",
            ),
        ),
    ]