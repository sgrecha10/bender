# Generated by Django 4.2.3 on 2024-05-12 22:22

from django.db import migrations

STRATEGY_CODENAME = 'default'

NAME = 'Последняя свеча для расчета'
CODENAME = 'average_price_last_candle'
VALUE = 'realtime'
DESCRIPTION = '''В реальном времени: 'realtime',
По последней закрытой свече: 'closed_candle',
'''


def code(apps, *_):
    Strategy = apps.get_model('strategies.Strategy')
    strategy = Strategy.objects.get(
        codename=STRATEGY_CODENAME,
    )

    AveragePrice = apps.get_model('indicators.AveragePrice')
    AveragePrice.objects.create(
        strategy=strategy,
        name=NAME,
        codename=CODENAME,
        value=VALUE,
        description=DESCRIPTION,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("indicators", "0002_auto_20240512_2321"),
    ]

    operations = [
        migrations.RunPython(code, atomic=True),
    ]