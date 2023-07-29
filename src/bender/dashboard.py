from grappelli.dashboard import modules, Dashboard


class IndexDashboard(Dashboard):

    def __init__(self, **kwargs):
        Dashboard.__init__(self, **kwargs)

        self.children.append(modules.AppList(
            title='Administration',
            column=1,
            collapsible=True,
            models=('django.contrib.*',),
        ))
