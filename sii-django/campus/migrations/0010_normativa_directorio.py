from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campus", "0009_retos_semanales"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentoNormativa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=200)),
                ("cuerpo", models.TextField(blank=True, default="")),
                ("archivo", models.FileField(blank=True, null=True, upload_to="normativa/%Y/%m/")),
                ("publicado", models.BooleanField(default=False)),
                ("autor_id", models.PositiveIntegerField(blank=True, null=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "campus_documento_normativa", "ordering": ["titulo"]},
        ),
        migrations.CreateModel(
            name="ContactoDirectorio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("area", models.CharField(max_length=80)),
                ("nombre", models.CharField(max_length=120)),
                ("medio", models.CharField(help_text="Correo, teléfono o horario.", max_length=160)),
                ("publicado", models.BooleanField(default=False)),
                ("autor_id", models.PositiveIntegerField(blank=True, null=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "campus_contacto_directorio", "ordering": ["area", "nombre"]},
        ),
    ]
