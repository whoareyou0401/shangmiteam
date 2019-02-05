import datetime
from django.core.cache import caches
from django.forms import model_to_dict

from .models import *
from django.http import JsonResponse, HttpResponse
from django.views.generic import View
user_cache = caches['user']
# cache = caches['default']

# 推广首页API
class StoreExpandIndexAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token"))
            )
        )
        store = user.store_set.all()[0]
        actives = store.activestoremap_set.filter(
            active__is_active=True
        )
        # 查看门店的推广金余额
        store_balance = store.storeactivebalance.balance

        # 获取免费推广时间
        free_hint = "经营推广功能90日内免费使用 到期时间" + str(store.free_date)

        # 判断是否有推广活动
        has_active_msg = False
        active = {}
        if actives.exists():
            has_active_msg = True

            active = model_to_dict(actives[0].active)

        data = {
            "code": 0,
            "data": {
                "has_active_msg":has_active_msg,
                "active": active,
                "free_hint": free_hint,
                "balance": "%.2f" % (store.storeactivebalance.balance / 100) ,
                "store_name": store.name,
                "user_balance": "%.2f" % (user.balance.money / 100)
            }
        }
        return JsonResponse(data)

# 门店将余额 转移到活动余额
class StoreActiveMoney(View):

    def post(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.POST.get("token"))
            )
        )
        # 单位是分
        money = int(float(req.POST.get("money")) * 100)
        if money <= 0:
            data = {
                "code": 1,
                "msg": "请充值大于0的金额"
            }
            return JsonResponse(data)
        if money > user.balance.money:
            data = {
                "code": 1,
                "msg": "余额不足，请先在个人中心充值"
            }
            return JsonResponse(data)
        store = user.store_set.all()[0]
        try:
            store_balance = StoreActiveBalance.objects.get(
                store=store
            )
        except:
            store_balance = StoreActiveBalance.objects.create(
                store=store,
                update_time=datetime.datetime.now()
            )
        # 活动余额增加
        store_balance.balance += money
        store_balance.save()
        # 用户余额减少
        user.balance.money -= money
        user.balance.save()
        data = {
            "code": 0,
            "msg": "充值成功"
        }
        return JsonResponse(data)

# 活动余额提现到账户余额
class StoreActiveGetMoney(View):

    def post(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.POST.get("token"))
            )
        )
        # 单位是分
        money = int(float(req.POST.get("money")) * 100)
        if money <= 0:
            data = {
                "code": 1,
                "msg": "请充值大于0的金额"
            }
            return JsonResponse(data)
        store = user.store_set.all()[0]
        if money > store.storeactivebalance.balance:
            data = {
                "code": 1,
                "msg": "金额不足"
            }
            return JsonResponse(data)

        store.storeactivebalance.balance -= money
        store.storeactivebalance.save()

        # 余额加钱
        user.balance.money += money
        user.balance.save()
        data = {
            "code": 0,
            "msg": "已提现到账户余额"
        }
        return JsonResponse(data)