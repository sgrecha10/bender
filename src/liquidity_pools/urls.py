from django.urls import path

from .views import ChartView

app_name = 'liquidity_pools'


urlpatterns = [
    path('chart/', ChartView.as_view(), name='chart'),
]
