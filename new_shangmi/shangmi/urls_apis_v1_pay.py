from .apis_v1_pay import *
from django.conf.urls import url
urlpatterns = [
    url(r"^pay$", pay_unifiedorder.as_view()),
    url(r"^order$", OrderAPI.as_view()),
    url(r"^notify$", PayNotifyAPI.as_view()),
    url(r"^get-money$", StoreGetMoneyAPI.as_view()),
    url(r"^user-get-money$", UserGetMoneyAPI.as_view()),
    url(r"^store-pay$", StoreRechargeAPI.as_view()),
    url(r"^store/notify$", StorePayNotifyAPI.as_view())
]