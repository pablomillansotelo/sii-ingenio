from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0010_aceptacion_carga"),
        ("ventas", "0006_datos_fiscales"),
    ]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="destacado",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="edicioncurso",
            name="educacion_continua",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="SolicitudOferta",
            fields=[
                ("id_solicitud", models.AutoField(primary_key=True, serialize=False)),
                (
                    "estado",
                    models.CharField(
                        choices=[("enviada", "Enviada"), ("atendida", "Atendida")],
                        default="enviada",
                        max_length=20,
                    ),
                ),
                ("creada_en", models.DateTimeField(auto_now_add=True)),
                ("atendida_en", models.DateTimeField(blank=True, null=True)),
                ("nota", models.TextField(blank=True, default="")),
                (
                    "alumno",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="solicitudes_oferta",
                        to="sii.alumno",
                    ),
                ),
                (
                    "edicion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="solicitudes",
                        to="ventas.edicioncurso",
                    ),
                ),
            ],
            options={
                "db_table": "solicitud_oferta",
                "ordering": ["-creada_en"],
                "unique_together": {("alumno", "edicion")},
            },
        ),
    ]
