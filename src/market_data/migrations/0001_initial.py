# Generated by Django 4.2.3 on 2023-08-25 22:53

import django.contrib.postgres.fields
import django.contrib.postgres.fields.hstore
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ExchangeInfo",
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
                (
                    "updated",
                    models.DateTimeField(auto_now=True, verbose_name="Дата обновления"),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Дата создания"
                    ),
                ),
                (
                    "rate_limits",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=django.contrib.postgres.fields.hstore.HStoreField(),
                        blank=True,
                        null=True,
                        size=None,
                        verbose_name="rate_limits",
                    ),
                ),
            ],
            options={
                "verbose_name": "Exchange Information",
                "verbose_name_plural": "Exchange Information",
            },
        ),
    ]