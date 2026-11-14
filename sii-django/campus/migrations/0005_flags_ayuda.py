from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("campus", "0004_preferencias"),
    ]

    operations = [
        migrations.AddField(
            model_name="campuspreferencia",
            name="ayuda_guiada",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="campuspreferencia",
            name="asistente_ia",
            field=models.BooleanField(default=False),
        ),
    ]
