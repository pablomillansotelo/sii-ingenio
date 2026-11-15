from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ventas", "0005_candado_academico"),
    ]

    operations = [
        migrations.AddField(model_name="cliente", name="rfc", field=models.CharField(blank=True, default="", max_length=13)),
        migrations.AddField(model_name="cliente", name="razon_social", field=models.CharField(blank=True, default="", max_length=160)),
        migrations.AddField(model_name="cliente", name="codigo_postal_fiscal", field=models.CharField(blank=True, default="", max_length=5)),
        migrations.AddField(model_name="cliente", name="regimen_fiscal", field=models.CharField(blank=True, default="", max_length=10)),
        migrations.AddField(model_name="cliente", name="factura_solicitada_en", field=models.DateTimeField(blank=True, null=True)),
    ]
