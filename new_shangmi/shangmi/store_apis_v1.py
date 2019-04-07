import datetime

from copy import deepcopy
from django.core.cache import caches
from django.core.paginator import Paginator
from django.forms import model_to_dict
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .paginations import LogPageNumberPagination
from .auth import LoginAuthentication
from .models import *
from django.http import JsonResponse, HttpResponse
from django.views.generic import View
from .serializers import *
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
        # print(req.session.get("ii"))
        try:
            store = Store.objects.get(boss=user)
        except:
            res = {"code": 2,
                   "msg":"您还没有门店"
                   }
            return JsonResponse(res)
        # actives = store.activestoremap_set.filter(
        #     active__is_active=True
        # )
        actives = ActiveStoreMap.objects.filter(
            store_id=store.id,
            active__is_active=True
        )
        # 查看门店的推广金余额
        if hasattr(store, "storeactivebalance"):
            store_balance = store.storeactivebalance.balance
        else:
            store_balance = 0

        # 获取免费推广时间
        free_hint = "经营推广功能90日内免费使用 到期时间" + str(store.free_date)

        # 判断是否有推广活动
        has_active_msg = False
        active = {}
        if actives.exists():
            has_active_msg = True

            active = model_to_dict(actives[0].active)
        if hasattr(user, "balance"):
            user_balance = store.balance
        else:
            user_balance = 0
        data = {
            "code": 0,
            "data": {
                "has_active_msg":has_active_msg,
                "active": active,
                "free_hint": free_hint,
                "balance": "%.2f" % (store_balance / 100) ,
                "store_name": store.name,
                "user_balance": "%.2f" % (user_balance / 100)
            }
        }
        result = JsonResponse(data)

        return result

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
        UserRecharge.objects.create(
            user_id=user.id,
            money=round(money / 100, 2),
            is_ok=True,
            wx_pay_num="9999",
            recharge_type="活动余额"
        )
        # 活动余额增加
        store_balance.balance += money
        store_balance.save()
        # 用户余额减少
        # user.balance.money -= money
        # user.balance.save()
        store.balance -= money
        store.save()

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
        store = user.store_set.all().first()
        if ActiveStoreMap.objects.filter(
            active__is_active=True,
            store_id=store.id
        ).exists():
            res = {
                "code": 2,
                "msg": "请先取消发布活动",
                "data": ""
            }
            return JsonResponse(res)
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
        # user.balance.money += money
        # user.balance.save()
        store.balance += money
        store.save()
        UserRecharge.objects.create(
            user_id=user.id,
            money=round(money/100, 2),
            is_ok=True,
            wx_pay_num="9999",
            recharge_type="账户余额"
        )
        data = {
            "code": 0,
            "msg": "已提现到账户余额"
        }
        return JsonResponse(data)

# 门店充值记录
class StoreUserRechargeAPI(ListAPIView):
    authentication_classes = [LoginAuthentication]
    pagination_class = LogPageNumberPagination
    queryset = UserRecharge.objects.filter(is_ok=True).order_by("-create_time")
    serializer_class = UserRechargeSerializer

    def list(self, request, *args, **kwargs):
        if not isinstance(self.request.user, ShangmiUser):
            return []
        queryset = self.get_queryset().filter(
                user_id=self.request.user.id
            )
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # return self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
        datas = []
        help = []
        for i in deepcopy(serializer.data):
            tmp = dict(i)
            tmp["date"], tmp['time'] = tmp.pop("create_time").split(" ")
            if tmp["date"] in help:
                tmp["show"] = False
            else:
                tmp["show"] = True
                help.append(tmp["date"])
            datas.append(tmp)
        result = {
            "code": 0,
            "msg": "ok",
            "data": datas
        }
        return Response(result)

# 门店收入明细
class StoreIncomeMoneyAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        page_num = int(req.GET.get("page", 1))
        store = user.store_set.all()[0]
        logs = UserPayLog.objects.filter(
            store=store,
            status=True
        ).order_by("-create_time")

        help = {}
        for i in logs:
            res = {}
            tmp = {}
            tmp["money"] = round((i.integral + i.money) / 100, 2)
            time = i.create_time.strftime("%Y年%m月%d日 %H:%M:%S")
            tmp["nick_name"] = i.user.nick_name[0] + "***"
            tmp["icon"] = i.user.icon
            tmp["date"] = time.split(" ")[0]
            tmp["time"] = time.split(" ")[1]
            if tmp["date"] in help:
                tmp_dict = help[tmp["date"]]
                tmp_dict["data"].append(tmp)
                tmp_dict["money"] = "%.2f" % (float(tmp_dict["money"]) + tmp["money"])
                help[tmp["date"]] = tmp_dict
            else:
                res["date"] = tmp["date"]
                res["data"] = [tmp]
                res["money"] = "%.2f" % float(tmp["money"])
                help[tmp["date"]] = res

        result = [{"date":k, "data": v, "num": len(v.get("data"))} for k, v in help.items()]
        result = sorted(result, key=lambda dic:dic["date"], reverse=True)
        if len(result[:page_num]) < 4:
            final_data = result[:page_num+1]
        else:
            final_data = result[:page_num]
        if len(result) == page_num:
            next = False
        else:
            next = True
        data = {
            "code": 0,
            "next":next,
            "data": final_data
        }
        return JsonResponse(data)

# 门店赏金明细
class StoreRewardDetailAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        page_num = int(req.GET.get("page", 1))
        if hasattr(user, "store_set"):
            store = user.store_set.all()[0]
        else:
            store = Store.objects.get(boss=user)
        logs = UserPayLog.objects.filter(
            store=store,
            status=True,
            money=0
        ).order_by("-create_time")
        help = {}
        for i in logs:
            res = {}
            tmp = {}
            tmp["money"] = round(i.integral  / 100, 2)
            time = i.create_time.strftime("%Y年%m月%d日 %H:%M:%S")
            tmp["nick_name"] = i.user.nick_name[0] + "***"
            tmp["icon"] = i.user.icon
            tmp["date"] = time.split(" ")[0]
            tmp["time"] = time.split(" ")[1]
            if tmp["date"] in help:
                tmp_dict = help[tmp["date"]]
                tmp_dict["data"].append(tmp)
                tmp_dict["money"] = "%.2f" % (float(tmp_dict["money"]) + tmp["money"])
                help[tmp["date"]] = tmp_dict
            else:
                res["date"] = tmp["date"]
                res["data"] = [tmp]
                res["money"] = "%.2f" % float(tmp["money"])
                help[tmp["date"]] = res

        result = [{"date":k, "data": v, "num": len(v.get("data"))} for k, v in help.items()]
        result = sorted(result, key=lambda dic:dic["date"], reverse=True)
        if len(result[:page_num]) < 4:
            final_data = result[:page_num+1]
        else:
            final_data = result[:page_num]
        if len(result) == page_num:
            next = False
        else:
            next = True
        data = {
            "code": 0,
            "next":next,
            "data": final_data
        }
        return JsonResponse(data)