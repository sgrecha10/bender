# Generated by Django 4.2.3 on 2024-09-17 20:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("indicators", "0005_movingaverage_interval_movingaverage_symbol"),
    ]

    operations = [
        migrations.AddField(
            model_name="movingaverage",
            name="make_self_df",
            field=models.BooleanField(default=False, verbose_name="Make self DF"),
        ),
    ]