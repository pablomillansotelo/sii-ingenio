from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0005_alumno_codigo_ingenio"),
    ]

    operations = [
        migrations.AddField(
            model_name="periodo",
            name="fecha_publicacion_calificaciones",
            field=models.DateField(
                blank=True,
                help_text="Fecha oficial de publicación de calificaciones. Si está vacía se usa el fin de periodo.",
                null=True,
            ),
        ),
    ]
