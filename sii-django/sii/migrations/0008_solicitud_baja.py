from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0007_alumno_contacto"),
    ]

    operations = [
        migrations.CreateModel(
            name="SolicitudBaja",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("motivo", models.TextField()),
                ("estado", models.CharField(choices=[("enviada", "Enviada"), ("aprobada", "Aprobada"), ("rechazada", "Rechazada")], default="enviada", max_length=20)),
                ("creada_en", models.DateTimeField(auto_now_add=True)),
                ("creada_por_id", models.PositiveIntegerField()),
                ("resuelta_en", models.DateTimeField(blank=True, null=True)),
                ("resuelta_por_id", models.PositiveIntegerField(blank=True, null=True)),
                ("comentario_staff", models.CharField(blank=True, default="", max_length=240)),
                ("alumno", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="solicitudes_baja", to="sii.alumno")),
                ("inscripcion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="solicitudes_baja", to="sii.inscripcion")),
            ],
            options={"db_table": "tra_solicitud_baja", "ordering": ["-creada_en"]},
        ),
    ]
