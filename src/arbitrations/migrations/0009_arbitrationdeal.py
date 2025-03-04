# Generated by Django 4.2.3 on 2025-01-05 18:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("market_data", "0001_initial"),
        ("arbitrations", "0008_alter_arbitration_ratio_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="ArbitrationDeal",
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
                ("deal_time", models.DateTimeField(verbose_name="Deal time")),
                (
                    "buy",
                    models.DecimalField(
                        blank=True,
                        decimal_places=10,
                        max_digits=20,
                        null=True,
                        verbose_name="Buy",
                    ),
                ),
                (
                    "sell",
                    models.DecimalField(
                        blank=True,
                        decimal_places=10,
                        max_digits=20,
                        null=True,
                        verbose_name="Sell",
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("close", "Close"),
                            ("profit", "Profit"),
                            ("loss", "Loss"),
                            ("unknown", "Unknown"),
                        ],
                        verbose_name="State",
                    ),
                ),
                (
                    "arbitration",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="arbitrations.arbitration",
                        verbose_name="Arbitration",
                    ),
                ),
                (
                    "symbol",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="market_data.exchangeinfo",
                        verbose_name="Symbol",
                    ),
                ),
            ],
            options={
                "verbose_name": "Arbitration Deal",
                "verbose_name_plural": "Arbitration Deals",
                "indexes": [
                    models.Index(
                        fields=["arbitration", "symbol", "deal_time"],
                        name="arbitration_arbitra_476443_idx",
                    )
                ],
            },
        ),
    ]
