from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ventas", "0004_ventadetalle_edicion_unica"),
    ]

    operations = [
        migrations.AddField(
            model_name="edicioncurso",
            name="candado_academico",
            field=models.BooleanField(
                default=False,
                help_text="Si está activo, oculta recursos de secciones aún no desbloqueadas. Por defecto el candado es solo lúdico.",
            ),
        ),
    ]
