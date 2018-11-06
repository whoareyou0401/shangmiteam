from apis_v2 import *
from django.conf.urls import url
urlpatterns = [
    url(r"^store/get_money$", store_get_money)
]