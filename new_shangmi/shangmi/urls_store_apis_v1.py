from django.conf.urls import url
from .store_apis_v1 import *
urlpatterns = [
    url(r"^expand$", StoreExpandIndexAPI.as_view()),
    url(r"^recharge$", StoreActiveMoney.as_view()),
    url(r"^get-money$", StoreActiveGetMoney.as_view())
]