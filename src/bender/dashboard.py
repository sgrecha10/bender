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
                'Кошелек',
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
                'Администрирование',
                column=2,
                collapsible=True,
                models=('django.contrib.*',),
            )
        )

        self.children.append(
            modules.LinkList(
                'Media Management',
                column=2,
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
        #     _('Recent actions'),
        #     limit=5,
        #     collapsible=False,
        #     column=3,
        # ))
