from django.core.management import BaseCommand

from liquidity_pools.models import StrategyCheck, Strategy


class Command(BaseCommand):
    help = 'Reset strategy check'

    def handle(self, *args, **kwargs):
        StrategyCheck.objects.all().delete()
        for strategy in Strategy.objects.all():
            StrategyCheck.objects.create(strategy=strategy)
