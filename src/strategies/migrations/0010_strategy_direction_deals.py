# Generated by Django 4.2.3 on 2024-12-03 16:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "strategies",
            "0009_remove_strategyresult_strategies__strateg_46b97a_idx_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="strategy",
            name="direction_deals",
            field=models.CharField(
                choices=[
                    ("default", "Default"),
                    ("only_sell", "Only sell"),
                    ("only_buy", "Only buy"),
                ],
                default="default",
                max_length=50,
                verbose_name="Direction deals",
            ),
        ),
    ]