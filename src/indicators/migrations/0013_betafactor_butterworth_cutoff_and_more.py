# Generated by Django 4.2.3 on 2025-02-10 14:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("indicators", "0012_betafactor_ema_span_alter_betafactor_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="betafactor",
            name="butterworth_cutoff",
            field=models.FloatField(default=0.05, verbose_name="Butterworth cutoff"),
        ),
        migrations.AddField(
            model_name="betafactor",
            name="butterworth_order",
            field=models.FloatField(
                default=3,
                help_text="✔ Для короткосрочного анализа (1-10 дней) → cutoff=0.1, order=3 ✔ Для среднесрочного анализа (10-50 дней) → cutoff=0.05, order=3-5 ✔ Для долгосрочного анализа (50+ дней) → cutoff=0.01, order=5-7",
                verbose_name="Butterworth order",
            ),
        ),
        migrations.AlterField(
            model_name="betafactor",
            name="type",
            field=models.CharField(
                choices=[
                    ("manual", "Manual"),
                    ("ols", "OLS"),
                    ("ema", "EMA"),
                    ("bw", "Butterworth"),
                ],
                default="ols",
                verbose_name="Type",
            ),
        ),
    ]
