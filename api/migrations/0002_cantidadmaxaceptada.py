# Generated by Django 3.2.4 on 2021-07-18 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CantidadMaxAceptada',
            fields=[
                ('tipo_oc', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('cantidad', models.IntegerField()),
            ],
        ),
    ]