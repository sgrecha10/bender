from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Strategy backtesting command'

    strategy_id = 1

    def handle(self, *args, **kwargs):
        from liquidity_pools.services.backtesting_service import BacktestingService

        backtesting_service = BacktestingService(
            strategy_id=self.strategy_id
        )
        backtesting_service.run_backtesting()
