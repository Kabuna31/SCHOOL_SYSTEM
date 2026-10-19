from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("examination", "0006_gradescale_level_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS examination_result CASCADE;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                CREATE TABLE examination_result (
                    id BIGSERIAL PRIMARY KEY,
                    school_id BIGINT NOT NULL REFERENCES administration_school(id) DEFERRABLE INITIALLY DEFERRED,
                    student_id BIGINT NOT NULL REFERENCES academic_student(id) DEFERRABLE INITIALLY DEFERRED,
                    subject_id BIGINT NOT NULL REFERENCES academic_subject(id) DEFERRABLE INITIALLY DEFERRED,
                    academic_year_id BIGINT NOT NULL REFERENCES administration_academicyear(id) DEFERRABLE INITIALLY DEFERRED,
                    term_id BIGINT REFERENCES administration_term(id) DEFERRABLE INITIALLY DEFERRED,
                    ca_score DOUBLE PRECISION,
                    exam_score DOUBLE PRECISION,
                    final_score DOUBLE PRECISION,
                    letter_grade VARCHAR(5),
                    points NUMERIC(4,2),
                    grade_scale_id BIGINT REFERENCES examination_gradescale(id) DEFERRABLE INITIALLY DEFERRED
                );
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                ALTER TABLE examination_result
                ADD CONSTRAINT unique_school_student_term_result
                UNIQUE (school_id, student_id, subject_id, academic_year_id, term_id);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS exam_result_student_idx ON examination_result(student_id);
                CREATE INDEX IF NOT EXISTS exam_result_subject_idx ON examination_result(subject_id);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]