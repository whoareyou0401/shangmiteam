from django.conf.urls import url
from .apis_v1 import *
urlpatterns = [
    url(r"^actives$", ActivesAPI.as_view()),
    url(r"^advs$", AdvAPI.as_view()),
    url(r"^login$", LoginAPI.as_view()),
    url(r"^home$", IndexAPI.as_view()),
    url(r"^active_detail$", UserActiveLogAPI.as_view()),
    url(r"^pay_detail$", UserPayLogAPI.as_view()),
    url(r"^task_detail$", TaskDetailAPI.as_view()),
    url(r"^active$", ActiveAPI.as_view()),
    url(r"^join$", JoinActiveAPI.as_view()),
    url(r"^active-qr$", QrcodeAPI.as_view()),
    url(r"^store$", StoreAPI.as_view()),
    url(r"^get-money-history$", UserGetMoneyLogAPI.as_view()),
    url(r"^store-join$", JoinStoreActiveAPI.as_view()),
    url(r"^test$", test),
    url(r"^store/actives$", StoreActive.as_view())
]