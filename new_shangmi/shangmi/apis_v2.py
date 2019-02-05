# 门店积分券的使用
from django.core.cache import caches
from django.http import JsonResponse
from django.views import View
from .models import ShangmiUser, Coupon

user_cache = caches['user']

def get_user(req):
    user = ShangmiUser.objects.get(
        pk=int(user_cache.get(
            req.GET.get("token")
        )
        )
    )
    return user
def post_user(req):
    user = ShangmiUser.objects.get(
        pk=int(user_cache.get(
            req.POST.get("token")
        )
        )
    )
    return user

class GetCoupon(View):
    def get(self, req):
        user = get_user(req)
        coupon_id = int(req.GET.get("c_id"))
        try:
            coupon = Coupon.objects.get()
        except:
            data = {
                "code": 1,
                "msg": "无此优惠券"
            }
            return JsonResponse