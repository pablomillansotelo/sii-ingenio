from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0010_aceptacion_carga"),
        ("campus", "0010_normativa_directorio"),
    ]

    operations = [
        migrations.CreateModel(
            name="TicketAyuda",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("folio", models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ("categoria", models.CharField(choices=[("academico", "Académico"), ("administrativo", "Administrativo"), ("tecnico", "Técnico"), ("otro", "Otro")], max_length=20)),
                ("asunto", models.CharField(max_length=160)),
                ("descripcion", models.TextField()),
                ("adjunto", models.FileField(blank=True, null=True, upload_to="ayuda/%Y/%m/")),
                ("estado", models.CharField(choices=[("abierto", "Abierto"), ("en_atencion", "En atención"), ("resuelto", "Resuelto"), ("cerrado", "Cerrado")], default="abierto", max_length=20)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("alumno", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tickets", to="sii.alumno")),
            ],
            options={"db_table": "campus_ticket_ayuda", "ordering": ["-creado_en"]},
        ),
        migrations.CreateModel(
            name="TicketRespuesta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("autor_id", models.PositiveIntegerField()),
                ("es_staff", models.BooleanField(default=False)),
                ("cuerpo", models.TextField()),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="respuestas", to="campus.ticketayuda")),
            ],
            options={"db_table": "campus_ticket_respuesta", "ordering": ["creado_en"]},
        ),
    ]
