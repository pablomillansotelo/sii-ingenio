from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campus", "0003_noticias"),
    ]

    operations = [
        migrations.CreateModel(
            name="CampusPreferencia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.PositiveIntegerField(unique=True)),
                ("tema", models.CharField(choices=[("claro", "Claro"), ("oscuro", "Oscuro")], default="claro", max_length=12)),
                ("acento", models.CharField(choices=[("rojo", "Rojo Ingenio"), ("vino", "Vino"), ("carbon", "Carbón"), ("arena", "Arena")], default="rojo", max_length=12)),
                ("animacion_carga", models.BooleanField(default=True)),
            ],
            options={"db_table": "campus_preferencia"},
        ),
    ]
