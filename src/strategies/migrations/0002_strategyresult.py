# Generated by Django 4.2.3 on 2024-09-22 20:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("market_data", "0001_initial"),
        ("strategies", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StrategyResult",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "server_time",
                    models.BigIntegerField(
                        blank=True, default=None, null=True, verbose_name="serverTime"
                    ),
                ),
                (
                    "updated",
                    models.DateTimeField(auto_now=True, verbose_name="Дата обновления"),
                ),
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Дата создания"
                    ),
                ),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=10, max_digits=20, verbose_name="Price"
                    ),
                ),
                (
                    "kline",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="market_data.kline",
                        verbose_name="Kline",
                    ),
                ),
                (
                    "strategy",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="strategies.strategy",
                        verbose_name="Strategy",
                    ),
                ),
            ],
            options={
                "verbose_name": "Strategy Result",
                "verbose_name_plural": "Strategy Results",
                "indexes": [
                    models.Index(
                        fields=["strategy", "kline"],
                        name="strategies__strateg_46b97a_idx",
                    )
                ],
            },
        ),
    ]