from django.db import migrations, models


def rellenar_codigos(apps, schema_editor):
    Alumno = apps.get_model("sii", "Alumno")
    for alumno in Alumno.objects.all():
        if not alumno.codigo_ingenio:
            alumno.codigo_ingenio = f"ING-{alumno.pk:06d}"
            alumno.save(update_fields=["codigo_ingenio"])


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0004_docente"),
    ]

    operations = [
        migrations.AddField(
            model_name="alumno",
            name="codigo_ingenio",
            field=models.CharField(
                blank=True,
                help_text="Identificador interno de Ingenio. No es una matrícula de otra institución.",
                max_length=20,
                null=True,
                unique=True,
            ),
        ),
        migrations.RunPython(rellenar_codigos, migrations.RunPython.noop),
    ]
