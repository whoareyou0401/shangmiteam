from django.forms import model_to_dict
from django.http import JsonResponse
from django.views.generic import View

from .models import *


class ActivesAPI(View):

    def get(self, req):

        actives = Active.objects.filter(
            is_active=True
        )
        fast = actives.filter(is_fast=True)
        unfast = actives.filter(is_fast=False)
        fast_data = [model_to_dict(i) for i in fast]
        unfast_data = [model_to_dict(i) for i in unfast]
        result = {
            "code": 1,
            "msg": "ok",
            "data": {
                "fast": fast_data,
                "unfast": unfast_data
            }
        }
        return JsonResponse(result)