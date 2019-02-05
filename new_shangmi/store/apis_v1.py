import qrcode
from django.core.cache import caches
from django.db.models import  Sum
from django.http import JsonResponse, HttpResponse, QueryDict
from django.views import View
import datetime
from shangmi.models import *
from django.core.paginator import Paginator
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
        # 计算免费拓展活动时间
        free_date = datetime.datetime.now() + datetime.timedelta(days=90)
        store.free_date = free_date
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
        logs = UserPayLog.objects.filter(
            store=store,
            create_time__gte=zore_now,
            create_time__lte=now,
            status=True
        )
        money = reward = 0
        for log in logs:
            money = money + log.integral + log.money
            reward += log.integral
        persons = logs.values('user_id').annotate(Sum('user_id'))
        data = {
            "code": 0,
            "data":{
                "amount": round((money+reward) / 100, 2),
                "reward": round(reward / 100, 2),
                "money":  round(money / 100, 2),
                "count": logs.count(),
                "persons": len(persons)
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


class BossInfoAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        user_info = {}
        user_info["nick_name"] = user.nick_name
        user_info["icon"] = user.icon
        user_info["phone"] = user.store_set.all().first().boss_phone
        user_info["balance"] = round(user.balance.money / 100, 2)
        store = user.store_set.all()[0] if len(user.store_set.all())>0 else None
        user_info["store_name"] = store.name if store else ""
        user_info["store_id"] = store.id if store else "暂无"
        user_info["receive"] = store.is_receive if store else False
        data = {
            "code": 0,
            "data": user_info
        }
        return JsonResponse(data)


class StoreRewardAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        page_num = int(req.GET.get("page"))
        nums = req.GET.get("nums")
        store = user.store_set.all()[0]
        logs = UserPayLog.objects.filter(
            store=store,
            status=True
        ).exclude(integral=0).order_by("-create_time")
        paginator = Paginator(logs, nums)

        log_data = []
        try:
            page = paginator.page(page_num)
            page_data = page.object_list
        except:
            data = {
                "code": 0,
                "data": []
            }
            return JsonResponse(data)
        for i in page_data:
            tmp = {}
            tmp["integral"] = round(i.integral / 100, 2)
            tmp["time"] = i.create_time.strftime("%Y年%m月%d日 %H:%M:%S")
            log_data.append(tmp)
        data = {
            "code": 0,
            "data": log_data
        }
        return JsonResponse(data)

class StoreIncomeMoneyAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        page_num = int(req.GET.get("page"))
        nums = req.GET.get("nums")
        store = user.store_set.all()[0]
        logs = UserPayLog.objects.filter(
            store=store,
            status=True
        ).order_by("-create_time")
        paginator = Paginator(logs, nums)

        log_data = []
        try:
            page = paginator.page(page_num)
            page_data = page.object_list
        except:
            data = {
                "code": 0,
                "data": []
            }
            return JsonResponse(data)
        for i in page_data:
            tmp = {}
            tmp["money"] = round((i.integral + i.money) / 100, 2)
            tmp["time"] = i.create_time.strftime("%Y年%m月%d日 %H:%M:%S")
            log_data.append(tmp)
        data = {
            "code": 0,
            "data": log_data
        }
        return JsonResponse(data)

class StoreReceiveNotice(View):

    def put(self, req):
        params = QueryDict(req.body)
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                params.get("token")
            )
            )
        )
        store = user.store_set.all()[0]
        store.is_receive = True if params.get("status") == "true" else False
        store.save()
        data = {
            "code": 0,
            "msg": "ok",
            "data": "ok"
        }
        return JsonResponse(data)