from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aula", "0001_consolidacion_plataforma"),
    ]

    operations = [
        migrations.AddField(
            model_name="calificacionactividad",
            name="entrega",
            field=models.TextField(blank=True, default=""),
        ),
    ]
