# Generated by Django 4.2.3 on 2024-10-30 19:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("strategies", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="strategy",
            name="fixed_bet_amount",
            field=models.DecimalField(
                decimal_places=10,
                default=1e-05,
                max_digits=20,
                verbose_name="Fixed bet amount",
            ),
        ),
        migrations.AddField(
            model_name="strategy",
            name="stop_loss_factor",
            field=models.DecimalField(
                decimal_places=4,
                default=1,
                max_digits=5,
                verbose_name="Stop loss factor",
            ),
        ),
        migrations.AddField(
            model_name="strategy",
            name="take_profit_factor",
            field=models.DecimalField(
                decimal_places=4,
                default=2,
                max_digits=5,
                verbose_name="Take profit factor",
            ),
        ),
    ]