# Generated by Django 4.2.3 on 2025-01-01 20:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("arbitrations", "0007_alter_arbitration_ratio_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="arbitration",
            name="ratio_type",
            field=models.CharField(
                choices=[("price", "By price ratio on opening deal")],
                default="price",
                help_text="Определение соотношения инструментов на входе в сделку",
                max_length=20,
                verbose_name="Ratio type",
            ),
        ),
    ]
