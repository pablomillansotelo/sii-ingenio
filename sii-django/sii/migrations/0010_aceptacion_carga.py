from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0009_documento_expediente"),
    ]

    operations = [
        migrations.AddField(
            model_name="periodo",
            name="ventana_aceptacion_inicio",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="periodo",
            name="ventana_aceptacion_fin",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="AceptacionCarga",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("estado", models.CharField(choices=[("aceptada", "Aceptada"), ("cambio", "Solicitud de cambio")], max_length=20)),
                ("acuse_en", models.DateTimeField(auto_now_add=True)),
                ("comentario", models.CharField(blank=True, default="", max_length=240)),
                ("inscripcion", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="aceptacion", to="sii.inscripcion")),
            ],
            options={"db_table": "tra_aceptacion_carga"},
        ),
    ]
