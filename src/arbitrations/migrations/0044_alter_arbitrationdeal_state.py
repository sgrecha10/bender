# Generated by Django 4.2.3 on 2025-03-11 19:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("arbitrations", "0043_rename_corr_stop_loss_arbitration_corr_stop_loss_value"),
    ]

    operations = [
        migrations.AlterField(
            model_name="arbitrationdeal",
            name="state",
            field=models.CharField(
                choices=[
                    ("open", "Open"),
                    ("close", "Close"),
                    ("correction", "Correction"),
                    ("stop_loss_corr", "Stop-loss by correlation"),
                ],
                verbose_name="State",
            ),
        ),
    ]
