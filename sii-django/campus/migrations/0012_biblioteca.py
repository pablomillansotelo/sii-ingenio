from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campus", "0011_tickets_ayuda"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecursoBiblioteca",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=200)),
                ("descripcion", models.TextField(blank=True, default="")),
                ("url", models.URLField(blank=True, default="")),
                ("archivo", models.FileField(blank=True, null=True, upload_to="biblioteca/%Y/%m/")),
                ("publicado", models.BooleanField(default=False)),
                ("autor_id", models.PositiveIntegerField(blank=True, null=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "campus_recurso_biblioteca", "ordering": ["titulo"]},
        ),
    ]
