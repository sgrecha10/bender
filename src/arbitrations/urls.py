from django.urls import path

from .views import ResultsView

urlpatterns = [
    path('results', ResultsView.as_view(), name='arbitration-results'),
]
