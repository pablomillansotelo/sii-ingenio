from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0008_solicitud_baja"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentoExpediente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("identificacion", "Identificación oficial"), ("domicilio", "Comprobante de domicilio"), ("certificado", "Certificado previo"), ("otro", "Otro")], max_length=30)),
                ("archivo", models.FileField(upload_to="expediente/%Y/%m/")),
                ("estado", models.CharField(choices=[("en_revision", "En revisión"), ("aceptado", "Aceptado"), ("rechazado", "Rechazado")], default="en_revision", max_length=20)),
                ("comentario_staff", models.CharField(blank=True, default="", max_length=240)),
                ("subido_en", models.DateTimeField(auto_now_add=True)),
                ("subido_por_id", models.PositiveIntegerField()),
                ("revisado_en", models.DateTimeField(blank=True, null=True)),
                ("revisado_por_id", models.PositiveIntegerField(blank=True, null=True)),
                ("alumno", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documentos", to="sii.alumno")),
            ],
            options={"db_table": "tra_documento_expediente", "ordering": ["-subido_en"]},
        ),
    ]
