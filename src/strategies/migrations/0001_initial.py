# Generated by Django 4.2.3 on 2024-09-14 12:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("indicators", "0003_remove_movingaverage_interval_and_more"),
        ("market_data", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Strategy",
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
                ("name", models.CharField(max_length=255, verbose_name="Name")),
                (
                    "description",
                    models.TextField(
                        blank=True, default="", verbose_name="Description"
                    ),
                ),
                (
                    "base_interval",
                    models.CharField(
                        choices=[
                            ("1m", "Minute 1"),
                            ("1h", "Hour 1"),
                            ("1d", "Day 1"),
                            ("1w", "Week 1"),
                            ("1M", "Month 1"),
                            ("1Y", "Year 1"),
                        ],
                        default="1m",
                        max_length=10,
                        verbose_name="Base interval",
                    ),
                ),
                (
                    "moving_average_1_interval",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("1m", "Minute 1"),
                            ("1h", "Hour 1"),
                            ("1d", "Day 1"),
                            ("1w", "Week 1"),
                            ("1M", "Month 1"),
                            ("1Y", "Year 1"),
                        ],
                        max_length=10,
                        null=True,
                        verbose_name="Interval",
                    ),
                ),
                (
                    "base_symbol",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="strategies_base_symbol",
                        to="market_data.exchangeinfo",
                        verbose_name="Base symbol",
                    ),
                ),
                (
                    "moving_average",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="indicators.movingaverage",
                        verbose_name="Moving Average",
                    ),
                ),
                (
                    "moving_average_symbol",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="strategies_ma_symbol",
                        to="market_data.exchangeinfo",
                        verbose_name="Symbol",
                    ),
                ),
            ],
            options={
                "verbose_name": "Strategy",
                "verbose_name_plural": "Strategies",
            },
        ),
    ]