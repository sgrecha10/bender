from django.urls import path
from .views import ChartView, ArbitrationChartView

urlpatterns = [
    path('chart', ChartView.as_view(), name='chart'),
    path('arbitration-chart', ArbitrationChartView.as_view(), name='arbitration_chart'),
]
