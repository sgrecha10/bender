# Generated by Django 4.2.3 on 2024-09-15 21:26

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("strategies", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="strategy",
            name="moving_average",
        ),
        migrations.RemoveField(
            model_name="strategy",
            name="moving_average_1_interval",
        ),
        migrations.RemoveField(
            model_name="strategy",
            name="moving_average_symbol",
        ),
    ]