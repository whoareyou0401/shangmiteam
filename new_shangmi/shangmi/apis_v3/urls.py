from django.conf.urls import url
from .apis import *
urlpatterns = [
    url(r"^baoxian$", BaoxianAPI.as_view()),
]