from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("docente", "0002_modelos_a_sii"),
        ("sii", "0003_identidad_actas_horario"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Docente",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("user_id", models.PositiveIntegerField(blank=True, null=True)),
                        ("nombre", models.CharField(max_length=100)),
                        ("apellido", models.CharField(max_length=100)),
                        ("email", models.EmailField(max_length=254, unique=True)),
                        ("telefono", models.CharField(blank=True, max_length=15, null=True)),
                        (
                            "especialidad",
                            models.CharField(blank=True, max_length=100, null=True),
                        ),
                        (
                            "estado",
                            models.CharField(
                                choices=[
                                    ("activo", "Activo"),
                                    ("inactivo", "Inactivo"),
                                    ("licencia", "En Licencia"),
                                ],
                                default="activo",
                                max_length=20,
                            ),
                        ),
                        ("fecha_ingreso", models.DateField(auto_now_add=True)),
                    ],
                    options={
                        "verbose_name": "Docente",
                        "verbose_name_plural": "Docentes",
                        "db_table": "cat_docente",
                        "managed": True,
                    },
                ),
                migrations.CreateModel(
                    name="DocenteCurso",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("fecha_asignacion", models.DateField(auto_now_add=True)),
                        ("es_coordinador", models.BooleanField(default=False)),
                        (
                            "curso",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="docentes_asignados",
                                to="sii.curso",
                            ),
                        ),
                        (
                            "docente",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="cursos_asignados",
                                to="sii.docente",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "Asignación Docente-Curso",
                        "verbose_name_plural": "Asignaciones Docente-Curso",
                        "db_table": "tra_docente_curso",
                        "managed": True,
                        "unique_together": {("docente", "curso")},
                    },
                ),
            ],
        ),
    ]
