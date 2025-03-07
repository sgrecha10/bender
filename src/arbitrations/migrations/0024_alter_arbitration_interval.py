# Generated by Django 4.2.3 on 2025-02-02 19:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("arbitrations", "0023_alter_arbitration_interval"),
    ]

    operations = [
        migrations.AlterField(
            model_name="arbitration",
            name="interval",
            field=models.CharField(
                choices=[
                    ("1min", "Minute 1"),
                    ("1h", "Hour 1"),
                    ("2h", "Hour 2"),
                    ("4h", "Hour 4"),
                    ("6h", "Hour 6"),
                    ("8h", "Hour 8"),
                    ("12h", "Hour 12"),
                    ("1D", "Day 1"),
                    ("1W", "Week 1"),
                    ("1M", "Month 1"),
                    ("1A", "Year 1"),
                ],
                default="1min",
                help_text="Влияет только на отображение результатов в чарте.",
                max_length=10,
                verbose_name="Base interval",
            ),
        ),
    ]
