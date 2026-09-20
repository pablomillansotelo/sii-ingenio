from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0001_initial"),
        ("ventas", "0002_alinear_columnas_produccion"),
    ]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="id_curso",
            field=models.OneToOneField(
                blank=True,
                db_column="id_curso_sii",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="oferta",
                to="sii.curso",
            ),
        ),
    ]
