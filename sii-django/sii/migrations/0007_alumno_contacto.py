from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0006_periodo_fecha_publicacion_calificaciones"),
    ]

    operations = [
        migrations.AddField(model_name="alumno", name="email_personal", field=models.EmailField(blank=True, default="", max_length=254)),
        migrations.AddField(model_name="alumno", name="direccion_calle", field=models.CharField(blank=True, default="", max_length=160)),
        migrations.AddField(model_name="alumno", name="colonia", field=models.CharField(blank=True, default="", max_length=80)),
        migrations.AddField(model_name="alumno", name="codigo_postal", field=models.CharField(blank=True, default="", max_length=5)),
        migrations.AddField(model_name="alumno", name="ciudad", field=models.CharField(blank=True, default="", max_length=80)),
        migrations.AddField(model_name="alumno", name="estado_domicilio", field=models.CharField(blank=True, default="", max_length=80)),
        migrations.AddField(model_name="alumno", name="empresa", field=models.CharField(blank=True, default="", max_length=120)),
        migrations.AddField(model_name="alumno", name="puesto", field=models.CharField(blank=True, default="", max_length=80)),
        migrations.AddField(model_name="alumno", name="telefono_laboral", field=models.CharField(blank=True, default="", max_length=15)),
        migrations.AddField(model_name="alumno", name="contacto_emergencia_nombre", field=models.CharField(blank=True, default="", max_length=120)),
        migrations.AddField(model_name="alumno", name="contacto_emergencia_telefono", field=models.CharField(blank=True, default="", max_length=15)),
    ]
