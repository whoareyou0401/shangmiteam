from django.conf.urls import url
from .apis_v1 import *
urlpatterns = [
    url(r"^actives$", ActivesAPI.as_view())
]