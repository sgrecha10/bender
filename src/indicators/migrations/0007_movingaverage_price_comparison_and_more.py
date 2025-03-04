# Generated by Django 4.2.3 on 2025-01-31 20:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("indicators", "0006_movingaverage_arbitration_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="movingaverage",
            name="price_comparison",
            field=models.CharField(
                choices=[
                    ("open_price", "Open price"),
                    ("close_price", "Close price"),
                    ("high_price", "High price"),
                    ("low_price", "Low price"),
                ],
                default="close_price",
                help_text="For Cross course",
                verbose_name="Price comparison",
            ),
        ),
        migrations.AlterField(
            model_name="movingaverage",
            name="interval",
            field=models.CharField(
                blank=True,
                choices=[
                    ("1T", "Minute 1"),
                    ("1H", "Hour 1"),
                    ("1D", "Day 1"),
                    ("1W", "Week 1"),
                    ("1M", "Month 1"),
                    ("1A", "Year 1"),
                ],
                max_length=10,
                null=True,
                verbose_name="Interval",
            ),
        ),
    ]
