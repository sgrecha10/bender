# Generated by Django 4.2.3 on 2024-12-04 20:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strategies", "0012_alter_strategy_direction_deals_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="strategy",
            name="maker_commission",
            field=models.DecimalField(
                decimal_places=3,
                default=0,
                max_digits=4,
                verbose_name="Maker commission",
            ),
        ),
        migrations.AddField(
            model_name="strategy",
            name="taker_commission",
            field=models.DecimalField(
                decimal_places=3,
                default=0,
                max_digits=4,
                verbose_name="Taker commission",
            ),
        ),
    ]
