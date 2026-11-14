from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campus", "0006_mensajes"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notificacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.PositiveIntegerField()),
                ("tipo", models.CharField(choices=[("actividad", "Actividad"), ("calificacion", "Calificación"), ("aviso", "Aviso"), ("deuda", "Saldo pendiente")], max_length=20)),
                ("clave", models.CharField(max_length=80)),
                ("titulo", models.CharField(max_length=200)),
                ("cuerpo", models.CharField(blank=True, default="", max_length=280)),
                ("url", models.CharField(blank=True, default="", max_length=200)),
                ("creada_en", models.DateTimeField(auto_now_add=True)),
                ("leida_en", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "campus_notificacion", "ordering": ["-creada_en"], "unique_together": {("user_id", "tipo", "clave")}},
        ),
    ]
