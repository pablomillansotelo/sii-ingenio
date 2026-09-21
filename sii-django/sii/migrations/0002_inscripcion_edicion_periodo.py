from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0001_initial"),
        ("ventas", "0004_ventadetalle_edicion_unica"),
    ]

    operations = [
        migrations.AddField(
            model_name="inscripcion",
            name="id_edicion",
            field=models.ForeignKey(
                blank=True,
                db_column="id_edicion",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="inscripciones_sii",
                to="ventas.edicioncurso",
            ),
        ),
        migrations.AddField(
            model_name="inscripcion",
            name="puede_cursar",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterUniqueTogether(
            name="inscripcion",
            unique_together={("alumno", "curso", "periodo")},
        ),
    ]
