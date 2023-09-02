from django.urls import path
from .views import DepthOfMarketView, GetRedisDataView, Dom


urlpatterns = [
    path('', DepthOfMarketView.as_view(), name='depth_of_market'),
    path('dom/', Dom.as_view(), name='dom'),
    path('get_redis_data/', GetRedisDataView.as_view(), name='get_redis_data'),  # данные для стакана
]
