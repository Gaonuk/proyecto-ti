# Generated by Django 3.2 on 2021-06-21 03:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recievedoc',
            name='anulacion',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='recievedoc',
            name='notas',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='recievedoc',
            name='rechazo',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='recievedoc',
            name='url_notificaion',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='sentoc',
            name='anulacion',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='sentoc',
            name='notas',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='sentoc',
            name='rechazo',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='sentoc',
            name='url_notificaion',
            field=models.TextField(blank=True),
        ),
    ]
