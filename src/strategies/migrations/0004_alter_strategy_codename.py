# Generated by Django 4.2.3 on 2024-11-19 05:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strategies", "0003_remove_strategy_name_strategy_codename"),
    ]

    operations = [
        migrations.AlterField(
            model_name="strategy",
            name="codename",
            field=models.CharField(
                max_length=255, unique=True, verbose_name="Codename"
            ),
        ),
    ]