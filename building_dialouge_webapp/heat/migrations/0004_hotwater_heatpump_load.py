# Generated by Django 5.0.8 on 2025-03-27 21:12

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('heat', '0003_photovoltaic'),
    ]

    operations = [
        migrations.CreateModel(
            name='Hotwater',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number_people', models.IntegerField()),
                ('profile', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), size=None)),
            ],
        ),
        migrations.CreateModel(
            name='Heatpump',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('medium', models.CharField()),
                ('type_temperature', models.CharField()),
                ('profile', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), size=None)),
            ],
            options={
                'unique_together': {('medium', 'type_temperature')},
            },
        ),
        migrations.CreateModel(
            name='Load',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number_people', models.IntegerField()),
                ('eec', models.IntegerField()),
                ('profile', django.contrib.postgres.fields.ArrayField(base_field=models.FloatField(), size=None)),
            ],
            options={
                'unique_together': {('number_people', 'eec')},
            },
        ),
    ]
