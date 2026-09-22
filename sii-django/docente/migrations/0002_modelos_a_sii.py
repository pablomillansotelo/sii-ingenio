from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("docente", "0001_consolidacion_plataforma"),
        ("sii", "0003_identidad_actas_horario"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="DocenteCurso"),
                migrations.DeleteModel(name="Docente"),
            ],
            database_operations=[],
        ),
    ]
