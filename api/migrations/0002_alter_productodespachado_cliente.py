# Generated by Django 3.2.4 on 2021-07-05 01:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productodespachado',
            name='cliente',
            field=models.CharField(max_length=30),
        ),
    ]