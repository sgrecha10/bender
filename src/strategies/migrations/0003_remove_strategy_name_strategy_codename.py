# Generated by Django 4.2.3 on 2024-11-19 05:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "strategies",
            "0002_strategy_fixed_bet_amount_strategy_stop_loss_factor_and_more",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="strategy",
            name="name",
        ),
        migrations.AddField(
            model_name="strategy",
            name="codename",
            field=models.CharField(
                max_length=255, null=True, unique=True, verbose_name="Codename"
            ),
        ),
    ]
