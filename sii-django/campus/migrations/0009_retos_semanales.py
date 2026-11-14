from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0010_aceptacion_carga"),
        ("campus", "0008_ludico"),
    ]

    operations = [
        migrations.CreateModel(
            name="RetoSemanal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("semana", models.DateField()),
                ("meta", models.PositiveIntegerField(default=1)),
                ("progreso", models.PositiveIntegerField(default=0)),
                ("completado_en", models.DateTimeField(blank=True, null=True)),
                ("alumno", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="retos_semanales", to="sii.alumno")),
                ("inscripcion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="retos_semanales", to="sii.inscripcion")),
            ],
            options={"db_table": "campus_reto_semanal", "ordering": ["semana", "id"], "unique_together": {("inscripcion", "semana")}},
        ),
    ]
