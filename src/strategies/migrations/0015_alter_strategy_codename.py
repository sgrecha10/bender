# Generated by Django 4.2.3 on 2024-12-05 12:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strategies", "0014_alter_strategy_codename"),
    ]

    operations = [
        migrations.AlterField(
            model_name="strategy",
            name="codename",
            field=models.CharField(
                choices=[("strategy_1", "Strategy_1"), ("strategy_anna", "Anna")],
                max_length=255,
                unique=True,
                verbose_name="Codename",
            ),
        ),
    ]
