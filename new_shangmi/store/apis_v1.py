import qrcode
from django.core.cache import caches
from django.http import JsonResponse, HttpResponse
from django.views import View
import datetime
from shangmi.models import *
from io import BytesIO

user_cache = caches["user"]
# 店老板绑定手机号
class BindStoreAPI(View):

    def post(self, req):
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            req.POST.get("token")
        )))
        phone = req.POST.get("phone")
        store = Store.objects.get(boss_phone=phone)
        store.boss=user
        store.is_active = True
        store.save()
        data = {
            "code": 0,
            "data":{
                "sid": store.id
            }
        }
        return JsonResponse(data)


class StoreTodayAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        store = user.store_set.all()[0]
        now = datetime.datetime.now()
        zore_now = now.replace(hour=0, minute=0, second=0)
        # 查看一个点
        print(now, zore_now)
        logs = UserPayLog.objects.filter(
            store=store,
            create_time__gte=zore_now,
            create_time__lte=now
        )
        reward = amount = 0
        for log in logs:
            amount = amount + log.integral + log.money
            reward += log.integral
        data = {
            "code": 0,
            "data":{
                "amount": amount / 100,
                "reward": reward / 100,
                "money": (amount - reward) / 100
            }
        }
        return JsonResponse(data)

class StoreQrcode(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        store = user.store_set.all()[0]
        url = "../pay_money/pay_money?store_id="+str(store.id)
        code_maker = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        # 填入在二维码中保存的数据
        code_maker.add_data(url)
        code_maker.make(fit=True)

        img = code_maker.make_image()
        buf = BytesIO()
        img.save(buf)
        return HttpResponse(buf.getvalue(), content_type="image/png")