from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ventas", "0003_producto_curso_sii"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="ventadetalle",
            unique_together={("id_venta", "id_producto", "id_edicion")},
        ),
    ]
