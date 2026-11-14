from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("campus", "0005_flags_ayuda"),
    ]

    operations = [
        migrations.CreateModel(
            name="Hilo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("asunto", models.CharField(max_length=160)),
                ("para_control", models.BooleanField(default=False)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("creado_por_id", models.PositiveIntegerField()),
            ],
            options={"db_table": "campus_hilo", "ordering": ["-creado_en"]},
        ),
        migrations.CreateModel(
            name="HiloParticipante",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.PositiveIntegerField()),
                ("hilo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participantes", to="campus.hilo")),
            ],
            options={"db_table": "campus_hilo_participante", "unique_together": {("hilo", "user_id")}},
        ),
        migrations.CreateModel(
            name="MensajeCampus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("autor_id", models.PositiveIntegerField()),
                ("cuerpo", models.TextField()),
                ("archivo", models.FileField(blank=True, null=True, upload_to="mensajes/%Y/%m/")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("hilo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="mensajes", to="campus.hilo")),
            ],
            options={"db_table": "campus_mensaje", "ordering": ["creado_en"]},
        ),
        migrations.CreateModel(
            name="MensajeLectura",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.PositiveIntegerField()),
                ("leido_en", models.DateTimeField(auto_now_add=True)),
                ("mensaje", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lecturas", to="campus.mensajecampus")),
            ],
            options={"db_table": "campus_mensaje_lectura", "unique_together": {("mensaje", "user_id")}},
        ),
    ]
