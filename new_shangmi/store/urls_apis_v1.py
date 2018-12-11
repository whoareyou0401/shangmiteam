from django.conf.urls import url
from .apis_v1 import *
urlpatterns = [
    url(r"^register$", BindStoreAPI.as_view()),
    url(r"^today$", StoreTodayAPI.as_view()),
    url(r"^qrcode$", StoreQrcode.as_view())
]
