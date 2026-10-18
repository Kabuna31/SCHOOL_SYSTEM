from django.db import migrations


O_LEVEL_RULES = [
    (80, 100, "A", 5),
    (70, 79.99, "B", 4),
    (60, 69.99, "C", 3),
    (50, 59.99, "D", 2),
    (0, 49.99, "E", 1),
]

A_LEVEL_RULES = [
    (80, 100, "A", 5),
    (70, 79.99, "B", 4),
    (60, 69.99, "C", 3),
    (50, 59.99, "D", 2),
    (0, 49.99, "E", 1),
]


def seed_scales(apps, schema_editor):
    # Skip the public schema — GradeScale is a tenant-app table and must only
    # be seeded inside tenant schemas, where migration 0006 actually added
    # the `level` column.
    if schema_editor.connection.schema_name == "public":
        return

    GradeScale = apps.get_model("examination", "GradeScale")
    GradeScaleRule = apps.get_model("examination", "GradeScaleRule")
    School = apps.get_model("administration", "School")

    def seed(level, name, rules):
        for school in School.objects.all():
            scale, _ = GradeScale.objects.get_or_create(
                school=school,
                name=name,
                defaults={"level": level},
            )
            for mn, mx, letter, pts in rules:
                GradeScaleRule.objects.get_or_create(
                    school=school,
                    grade_scale=scale,
                    min_grade=mn,
                    max_grade=mx,
                    defaults={
                        "letter_grade": letter,
                        "numeric_scale": pts,
                    },
                )

    seed("O", "New Lower Secondary (UCE)", O_LEVEL_RULES)
    seed("A", "Proposed UACE (2028)", A_LEVEL_RULES)


def unseed_scales(apps, schema_editor):
    if schema_editor.connection.schema_name == "public":
        return

    GradeScale = apps.get_model("examination", "GradeScale")
    GradeScale.objects.filter(
        name__in=["New Lower Secondary (UCE)", "Proposed UACE (2028)"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("examination", "0006_gradescale_level_and_more"),
        ("administration", "0003_school_class_teacher_signature_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_scales, unseed_scales),
    ]