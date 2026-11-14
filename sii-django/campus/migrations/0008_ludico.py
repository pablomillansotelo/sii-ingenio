from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("sii", "0010_aceptacion_carga"),
        ("campus", "0007_notificaciones"),
    ]

    operations = [
        migrations.CreateModel(
            name="PerfilLudico",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("xp", models.PositiveIntegerField(default=0)),
                ("monedas", models.PositiveIntegerField(default=0)),
                ("ranking_publico", models.BooleanField(default=False)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("reset_en", models.DateTimeField(blank=True, null=True)),
                ("reset_por_id", models.PositiveIntegerField(blank=True, null=True)),
                ("alumno", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="perfil_ludico", to="sii.alumno")),
            ],
            options={"db_table": "campus_perfil_ludico"},
        ),
        migrations.CreateModel(
            name="Insignia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("clave", models.CharField(max_length=40, unique=True)),
                ("nombre", models.CharField(max_length=80)),
                ("descripcion", models.CharField(blank=True, default="", max_length=200)),
            ],
            options={"db_table": "campus_insignia"},
        ),
        migrations.CreateModel(
            name="InsigniaAlumno",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("obtenida_en", models.DateTimeField(auto_now_add=True)),
                ("insignia", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="campus.insignia")),
                ("perfil", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="insignias", to="campus.perfilludico")),
            ],
            options={"db_table": "campus_insignia_alumno", "unique_together": {("perfil", "insignia")}},
        ),
        migrations.CreateModel(
            name="MovimientoXP",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cantidad", models.IntegerField()),
                ("motivo", models.CharField(max_length=160)),
                ("clave", models.CharField(max_length=80)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("creado_por_id", models.PositiveIntegerField(blank=True, null=True)),
                ("perfil", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="movimientos", to="campus.perfilludico")),
            ],
            options={"db_table": "campus_movimiento_xp", "ordering": ["-creado_en"], "unique_together": {("perfil", "clave")}},
        ),
    ]
