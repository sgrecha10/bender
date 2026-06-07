from django.core.management import BaseCommand
from liquidity_pools.services.pool_strategy_backtesting_service import PoolStrategyBacktestingService
from liquidity_pools.models import Strategy


class Command(BaseCommand):
    help = 'Strategy backtesting command'

    strategy_id = 1

    def handle(self, *args, **kwargs):
        backtesting_service = PoolStrategyBacktestingService(
            strategy_id=self.strategy_id
        )
        backtesting_service.run_backtesting()
