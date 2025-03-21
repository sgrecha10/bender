# Generated by Django 4.2.3 on 2025-03-10 19:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("arbitrations", "0041_alter_arbitration_corr_open_deal_value_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="arbitration",
            name="corr_stop_loss",
            field=models.FloatField(
                default=0.85,
                help_text="Значение корреляции для срабатывания stop loss, менее. Если 0 - не используется.",
                verbose_name="Corr stop loss value",
            ),
        ),
    ]
