from grappelli.dashboard import Dashboard, modules

# from grappelli.dashboard.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """

    def init_with_context(self, context):
        # site_name = get_admin_site_name(context)

        self.children.append(
            modules.AppList(
                'WALLET',
                column=1,
                collapsible=True,
                models=(
                    'wallet.models.SpotBalance',
                    'wallet.models.TradeFee',
                ),
            )
        )

        self.children.append(
            modules.AppList(
                'MARKET DATA',
                column=1,
                collapsible=True,
                models=(
                    'market_data.models.ExchangeInfo',
                    'market_data.models.Kline',
                ),
            )
        )

        self.children.append(
            modules.AppList(
                'INDICATORS',
                column=1,
                collapsible=True,
                models=(
                    'indicators.models.MovingAverage',
                    'indicators.models.StandardDeviation',
                    'indicators.models.BollingerBands',
                    'indicators.models.BetaFactor',
                ),
            )
        )

        self.children.append(
            modules.AppList(
                'STRATEGIES',
                column=1,
                collapsible=True,
                models=(
                    'strategies.models.Strategy',
                    'strategies.models.StrategyResult',
                ),
            )
        )
        self.children.append(
            modules.AppList(
                'ARBITRATIONS',
                column=1,
                collapsible=True,
                models=(
                    'arbitrations.models.Arbitration',
                    'arbitrations.models.ArbitrationDeal',
                ),
            )
        )
        self.children.append(
            modules.AppList(
                'DEFI',
                column=1,
                collapsible=True,
                models=(
                    'defi.models.UniswapPool',
                    'defi.models.MempoolTransaction',
                    'defi.models.SwapChain',
                ),
            )
        )

        self.children.append(
            modules.AppList(
                'WEBSOCKET',
                column=2,
                collapsible=True,
                models=(
                    'streams.models.TaskManagement',
                ),
            )
        )

        self.children.append(
            modules.LinkList(
                'HANDLERS',
                column=2,
                children=[
                    {
                        'title': 'Запустить поток',
                        'url': '/streams?action=start',
                        'external': False,
                    },
                    {
                        'title': 'Остановить поток',
                        'url': '/streams?action=stop',
                        'external': False,
                    },
                    {
                        'title': 'Стакан',
                        'url': '/streams/dom/',
                        'external': False,
                    },
                ],
            ),
        )

        self.children.append(
            modules.AppList(
                'Администрирование',
                column=3,
                collapsible=True,
                models=('django.contrib.*',),
            )
        )

        self.children.append(
            modules.LinkList(
                'Media Management',
                column=3,
                children=[
                    {
                        'title': 'FileBrowser',
                        'url': '/admin/filebrowser/browse/',
                        'external': False,
                    },
                ],
            )
        )

        self.children.append(
            modules.LinkList(
                'Support',
                column=3,
                children=[
                    {
                        'title': 'Django Documentation',
                        'url': 'http://docs.djangoproject.com/',
                        'external': True,
                    },
                    {
                        'title': 'Grappelli Documentation',
                        'url': 'http://packages.python.org/django-grappelli/',
                        'external': True,
                    },
                    {
                        'title': 'Grappelli Google-Code',
                        'url': 'http://code.google.com/p/django-grappelli/',
                        'external': True,
                    },
                ],
            )
        )

        # self.children.append(modules.RecentActions(
        #     'Recent actions',
        #     limit=5,
        #     collapsible=False,
        #     column=3,
        # ))
