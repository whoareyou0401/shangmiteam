import io
import json

import random
import requests

from django.core.paginator import Paginator
from django.db.models import Sum
from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.views.generic import View

from .idcard_util import check_id
from .utils import *
from .models import *
from django.core.cache import caches
from .getqr import *
import uuid
import datetime
from .WXBizDataCrypt import *
from io import BytesIO
import oss2
from django.db import connection
from django.conf import settings
from .baoxian_util import submit_one
from .checkIdcard import IDnumber

user_cache = caches['user']
cache = caches['default']
class LoginAPI(View):

    def post(self, request):

        params = request.POST
        code = params.get('code')
        avatar = params.get('avatar')
        iv = params.get('iv', "")
        encryptedData = params.get("encryptedData", "")
        nick_name = params.get('name')
        mini_type = params.get('mini_type')
        token = params.get("token")
        user_id = user_cache.get(token)
        if user_id:
            user_cache.set(token, user_id, settings.LOGIN_TIMEOUT)
            return JsonResponse({'code': 0, 'data': {'token': token, "uid": user_id}})
        if mini_type == 'background':
            appid = 'wx4a8c99d5d8b43556'
            secret = '014ad578b31357e53b61b9ab69db0761'
        elif mini_type == 'customer':
            appid = 'wx8b50ab8fa813a49e'
            secret = 'b32f63c36ea123710173c4c9d4b15e8b'
        else:
            appid = 'wxebd828458f8b2b38'
            secret = 'a40cb9c5ecb1f4f5c0f31b75829fed03'
        url = settings.SMALL_WEIXIN_OPENID_URL
        params = {"appid": appid,
                  "secret": secret,
                  "js_code": code,
                  "grant_type": 'authorization_code'
                  }
        response = requests.get(url, params=params)

        data = json.loads(response.content.decode())
        # session_key = data.get("session_key")
        # pc = WXBizDataCrypt(appid, session_key)

        # print(pc.decrypt(encryptedData, iv))
        # decrypt_data = pc.decrypt(encryptedData, iv)
        if 'openid' in data:
            openid = data.get('openid')
            user = ShangmiUser.objects.get_or_create(openid=openid)[0]
            # token = generate_validate_token(str(user.id))
            token = uuid.uuid4().hex
            user_cache.set(token, user.id, settings.LOGIN_TIMEOUT)
            user.nick_name = nick_name
            user.icon = avatar
            user.source = mini_type
            user.save()
            return HttpResponse(json.dumps({'code': 0, 'data': {'token': token, "uid": user.id}}),
                                content_type='application/json')
        else:
            return HttpResponse(json.dumps({'code': 1, 'msg': '登录失败，请回到首页'}),
                                content_type='application/json')

class ActivesAPI(View):

    def get(self, req):

        actives = Active.objects.filter(
            is_active=True
        )
        fast = actives.filter(is_fast=True)
        unfast = actives.filter(is_fast=False)
        # fast_data = [model_to_dict(i) for i in fast]
        unfast_data = [model_to_dict(i) for i in unfast]
        fast_data = []
        for i in fast:
            tmp = model_to_dict(i)
            if i.need_num == 0:
                tmp["percent"] = "30"
            else:
                tmp["percent"] = round((i.complete_num / i.need_num) * 100, 2)
                if tmp["percent"]<40:
                    tmp["percent"] = random.randint(30, 40)
            fast_data.append(tmp)
        unfast_data = []
        for i in unfast:
            tmp = model_to_dict(i)
            if i.need_num == 0:
                tmp["percent"] = "30"
            else:
                tmp["percent"] = round((i.complete_num / i.need_num), 2) * 100
                if tmp["percent"]<30:
                    tmp["percent"] = 30
            unfast_data.append(tmp)
        result = {
            "code": 1,
            "msg": "ok",
            "data": {
                "fast": fast_data,
                "unfast": unfast_data,
                "phone": "010-59440917",
                "title": {
                    "first":"快快领",
                    "last": "慢慢攒"
                }
            }
        }
        return JsonResponse(result)


class AdvAPI(View):

    def get(self,req):
        advs = Advertise.objects.filter(
            is_used=True
        )
        res = [model_to_dict(i) for i in advs]
        data = {
            "code":1,
            "msg": "ok",
            "data": res,
            "hint": "领钱",
            "scan": "支付"
        }
        return JsonResponse(data)

class IndexAPI(View):
    # @login_req
    def get(self, req):
        # print(req.GET.get("token"))
        user = ShangmiUser.objects.get(pk=int(user_cache.get(req.GET.get("token"))))
        actives = UserActiveLog.objects.filter(user=user)
        # 未通过的
        doing_count = actives.filter(status=0).count()
        # 审核通过的
        finish_count = actives.filter(status=1).count()
        # 用户余额
        now = datetime.datetime.now()
        zero_now = now.replace(hour=0, minute=0, second=0)
        today = actives.filter(
            create_time__gte=zero_now,
            create_time__lte=now,
            status=True
        ).aggregate(Sum("integral")).get("integral__sum")

        if not today:
            today = "0.00"
        else:
            today = '%.2f' % (today / 100)
        try:
            money = Balance.objects.get(user=user).money
        except:
            money = 0
        data = {
            "code": 0,
            "data": {
                'money': '%.2f' % (money / 100),
                'doing_count': doing_count,
                'finish_count': finish_count,
                "today": today,
                "is_show": True,
                "is_show_tixian": True,
                "wechat": "Eternal_love2012",
                "option":{
                    "t1":"今日收益",
                    "t2": "提现",
                    "t3": "收入明细",
                    "t4": "任务明细",
                    "t5": "付款记录",
                    "t6": "提现记录"
                }
            }
        }
        return JsonResponse(data)


# 用户参加活动明细
class UserActiveLogAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
                )
            )
        )
        logs = UserActiveLog.objects.filter(
            user=user,
            status=1
        ).order_by("-create_time")
        data_logs = []
        page_num = int(req.GET.get("page"))
        nums = req.GET.get("nums")
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
        # datas = []
        help = []
        for i in page_data:
            tmp = model_to_dict(i)
            if i.create_time.date() in help:
                tmp["show"] = False
            else:
                tmp["show"] = True
                help.append(i.create_time.date())
            time_str = i.create_time.strftime("%Y年%m月%d日 %H:%M:%S")
            tmp["date"] = time_str.split(" ")[0]

            tmp['time'] = time_str.split(" ")[-1]
            tmp["status"] = i.status
            tmp["active_msg"] = model_to_dict(i.active)
            tmp["type"] = i.get_type_display()
            data_logs.append(tmp)

        return JsonResponse({"code": 0, "data": data_logs})


# 付款明细
class UserPayLogAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        logs = UserPayLog.objects.filter(user=user, status=1).order_by("-create_time")
        help = []
        datas = []
        page_num = int(req.GET.get("page"))
        nums = req.GET.get("nums")
        paginator = Paginator(logs, nums)
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
            tmp = model_to_dict(i)
            if i.create_time.date() in help:
                tmp["show"] = False
            else:
                tmp["show"] = True
                help.append(i.create_time.date())
            time_str = i.create_time.strftime("%Y年%m月%d日 %H:%M:%S")
            tmp["date"] = time_str.split(" ")[0]

            tmp['time'] = time_str.split(" ")[-1]
            tmp["store_name"] = i.store.name
            tmp["money"] = "%.2f" % (i.money / 100)
            tmp["integral"] = "%.2f" % (i.integral / 100)
            tmp.pop("order_num")
            datas.append(tmp)

        data = {
            "code": 0,
            "data": datas
        }
        return JsonResponse(data)

# 任务明细
class TaskDetailAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        datas = UserActiveLog.objects.filter(user=user).order_by("-create_time")
        details = []
        page_num = int(req.GET.get("page"))
        nums = req.GET.get("nums")
        paginator = Paginator(datas, nums)
        help = []
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
            tmp = model_to_dict(i)
            if i.create_time.date() in help:
                tmp["show"] = False
            else:
                tmp["show"] = True
                help.append(i.create_time.date())
            time_str = i.create_time.strftime("%Y年%m月%d日 %H:%M:%S")
            tmp["date"] = time_str.split(" ")[0]

            tmp['time'] = time_str.split(" ")[-1]
            # tmp['create_time'] = i.create_time.strftime("%Y年%m月%d日 %H:%M")
            tmp["status"] = i.status
            tmp["active_msg"] = model_to_dict(i.active)
            tmp["type"] = i.get_type_display()
            details.append(tmp)

        data = {
            "code": 0,
            "data": details
        }
        return JsonResponse(data)

class ActiveAPI(View):

    def get(self, req):
        id = int(req.GET.get("id"))
        active = Active.objects.get(pk=id)
        data = {
            "code": 0,
            "data": model_to_dict(active)
        }
        return JsonResponse(data)

    # 创建活动
    def post(self, req):
        params = req.POST
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            req.POST.get("token")
        )))
        if not Store.objects.filter(boss=user).exists():
            data = {
                "code": 2,
                "msg": "您不是店老板"
            }
            return JsonResponse(data=data)
        name = params.get("name","")+"推广"
        lat = params.get("lat", 0)
        lng = params.get("lng", 0)
        if params.get("range") == "不限制":
            range = 10000000
        else:
            range = params.get("range").split("公里")[0]
        # 赏金
        givemoney = params.get("givemoney")
        if float(givemoney) <= 0:
            data = {
                "code": 1,
                "msg": "赏金不能为0"
            }
            return JsonResponse(data)
        # 分享送赏金
        share_give_money = params.get("share_give_money", 0)
        # 红包数量
        need_num = params.get("need_num")
        rule = params.get("rule", "")
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            req.POST.get("token")
        )))
        # 活动描述
        desc = params.get("desc", "")
        address = params.get("addr", "")
        # icon = req.FILES.get("file")
        # 将图片传到阿里云
        store = user.store_set.all()[0]
        if store.activestoremap_set.filter(active__is_active=True).exists():
            data = {
                "code": 1,
                "msg": "您已经发布过活动了"
            }
            return JsonResponse(data)
        my_file = req.FILES.get("img")
        # 实例化一个比特流的缓存区
        my_buf = io.BytesIO()

        # 将文件数据写入到缓存区
        for i in my_file.chunks():
            my_buf.write(i)
        # 将文件指针指会缓冲区的头
        my_buf.seek(0)

        # 调用oss的API

        # oss认证
        auth = oss2.Auth(
            settings.OSS_ACCESS_KEY_ID,
            settings.OSS_ACCESS_KEY_SECRET
        )
        bucket_name = 'shangmi'
        # 获得存储桶
        bucket = oss2.Bucket(
            auth,
            "https://oss-cn-beijing.aliyuncs.com",
            bucket_name
        )

        # 获取文图片件后缀
        remote_file_name = "apps/"+get_unique_name() + "." + my_file.name.split(".")[-1]
        bucket_name_host = "shangmi.oss-cn-beijing.aliyuncs.com"
        # 拼接图片远端的url
        img_url = "https://{host}/{file_name}".format(
            host=bucket_name_host,
            file_name=remote_file_name
        )

        # 将缓存的数据传到oss上
        bucket.put_object(remote_file_name, my_buf.getvalue())
        if rule == "":
            rule = str(range)+"公里内的用户可参与"
#         创建活动
        active = Active.objects.get_or_create(
            name=name,
            icon=img_url,
            detail_icon=img_url,
            desc=desc,
            need_num=need_num,
            share_give_money=share_give_money*100,
            rule=rule,
            give_money=float(givemoney)*100,
            is_active=False,
            lat=lat,
            lng=lng,
            range=range,
            address=address,
            detail_url="../storeJoin/storeJoin"
        )[0]
#         创建活动与门店的关系映射 方便门店查看我发起的活动
        store_active_map = ActiveStoreMap.objects.get_or_create(
            store=store,
            active=active
        )
        data = {
            "code": 0,
            "data": "ok",
            "msg": "创建成功，请等待审核"
        }
        send_mymail(store, active.name)
        return JsonResponse(data)

    def put(self, req):
        params = QueryDict(req.body)
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            params.get("token")
        )))
        aid = int(params.get("aid"))
        store = user.store_set.all()[0]
        if ActiveStoreMap.objects.filter(store_id=store.id, active_id=aid).exists():
            active = store.activestoremap_set.all().filter(active_id=aid).first().active
            active.is_active = not active.is_active
            active.save()
            data = {
                "code": 0,
                "data": {
                    "is_active": active.is_active
                }
            }
            return JsonResponse(data)
        else:
            data = {
                "code": 2,
                "data":{},
                "msg": "无此活动"
            }
            return JsonResponse(data)

class ShareGetMoneyAPI(View):

    def post(self, req):
        token = req.POST.get("token")
        share_uid = req.POST.get("uid")
        user = user_cache.get()


class JoinActiveAPI(View):

    def post(self, req):

        user = ShangmiUser.objects.get(pk=int(user_cache.get(
                req.POST.get("token")
            )))
        uid = req.POST.get("uid")
        id = req.POST.get("id")
        active = Active.objects.get(id=id)
        if active.is_active == False:
            data = {
                "code": 3,
                "data": "活动已结束"
            }
            return JsonResponse(data)
        # 先判断该用户是不是已经参与了
        if UserActiveLog.objects.filter(user_id=user.id).exists():
            data = {
                "code": 2,
                "data": "您已参加，想赚更多可分享"
            }
            return JsonResponse(data)
        log = UserActiveLog.objects.create(
            active_id=id,
            user_id=user.id,
            integral=active.give_money,
            type="join",
            status=1
        )
        active.complete_num += 1
        active.save()
        # 更新用户余额表
        user_balance = Balance.objects.get_or_create(user_id=user.id)[0]
        user_balance.money += active.give_money
        user_balance.save()
        if int(uid) != -1 and int(uid) != user.id:
            UserActiveLog.objects.create(
                active_id=id,
                user_id=uid,
                integral=active.share_give_money,
                type="share",
                status=1
            )
            # 更新分享人用户积分余额
            share_user_balance = Balance.objects.get(user_id=uid)
            share_user_balance.money += active.share_give_money
            share_user_balance.save()
        # 判断活动是不是要结束
        if active.complete_num == active.need_num:
            active.is_active = False
            active.save()
        data = {
            "code": 0,
            "data": "参与成功，积分已发放到个人中心"
        }
        return JsonResponse(data)


class JoinStoreActiveAPI(View):

    def post(self, req):

        user = ShangmiUser.objects.get(pk=int(user_cache.get(
                req.POST.get("token")
            )))
        uid = req.POST.get("uid")
        id = req.POST.get("id")
        active = Active.objects.get(id=id)
        sa_map = ActiveStoreMap.objects.get(active_id=active.id)
        lat = req.POST.get("lat")
        lng = req.POST.get("lng")
        # 获取经纬度 计算距离
        if lat and lng:
            if active.lng and active.lat:
                haversine(float(lng), float(lat), active.lng, active.lat)
            #     保存用户位置
            user.lat = lat
            user.lng = lng
            user.save()
        else:
            data = {
                "code": 2,
                "data": "",
                "msg": "请先获取位置"
            }
            return JsonResponse(data)
        if sa_map.store.storeactivebalance.balance < (active.give_money + active.share_give_money):
            data = {
                "code": 1,
                "msg": "活动暂时停止"
            }
            send_my_store_mail(sa_map.store, active.name)
            return JsonResponse(data)


        if active.is_active == False:
            data = {
                "code": 3,
                "msg": "活动已结束"
            }
            return JsonResponse(data)
        # 先判断该用户是不是已经参与了
        if UserActiveLog.objects.filter(user_id=user.id, active_id=active.id).exists():
            data = {
                "code": 2,
                "msg": "您已参加，想赚更多可分享"
            }
            return JsonResponse(data)
        log = UserActiveLog.objects.create(
            active_id=id,
            user_id=user.id,
            integral=active.give_money,
            type="join",
            status=1
        )
        active.complete_num += 1
        active.save()
        # 更新用户余额表
        user_balance = Balance.objects.get_or_create(user_id=user.id)[0]
        user_balance.money += active.give_money
        user_balance.save()

        # 给门店活动减钱

        store_balance = sa_map.store.storeactivebalance
        store_balance.balance = store_balance.balance - active.give_money

        if int(uid) != -1 and int(uid) != user.id:
            UserActiveLog.objects.create(
                active_id=id,
                user_id=uid,
                integral=active.share_give_money,
                type="share",
                status=1
            )
            # 更新分享人用户积分余额
            share_user_balance = Balance.objects.get(user_id=uid)
            share_user_balance.money += active.share_give_money
            share_user_balance.save()
            store_balance.balance -= active.share_give_money
        #     保存门店余额
        store_balance.save()
        # 判断活动是不是要结束
        if active.complete_num == active.need_num:
            active.is_active = False
            active.save()

        data = {
            "code": 0,
            "msg": "参与成功，积分已发放到个人中心"
        }
        return JsonResponse(data)


class QrcodeAPI(View):
    def get(self, request):
        params = request.GET
        store_id = int(params.get('store_id'))

        wx_mini_path = 'pages/index/index?store_id=%s' % store_id
        image_data = get_qrcode(wx_mini_path)
        return HttpResponse(image_data,content_type="image/png")


class StoreAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        balance = Balance.objects.get_or_create(user_id=user.id)[0]
        store_id = int(req.GET.get("sid"))
        store = Store.objects.get(id=store_id)
        if store.is_active == False:
            data = {
                "code": 2,
                "data": "该店暂不参与"
            }
            return JsonResponse(data)
        else:
            store_dict = model_to_dict(store)
            store_dict["boss_name"] = store.boss.nick_name
            store_dict["boss_icon"] = store.boss.icon
            store_dict["user_balance"] = balance.money / 100
            return JsonResponse({"code": 0, "data": store_dict})


# 用户提现记录
class UserGetMoneyLogAPI(View):
    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        page_num = int(req.GET.get("page"))
        nums = req.GET.get("nums")
        logs = GetMoneyLog.objects.filter(
            user=user,
            is_ok=True
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
        datas = []
        help = []
        for i in page_data:
            tmp = {}
            if i.create_time.date() in help:
                tmp["show"] = False
            else:
                tmp["show"] = True
                help.append(i.create_time.date())
            time_str = i.create_time.strftime("%Y年%m月%d日 %H:%M:%S")
            tmp["date"] = time_str.split(" ")[0]
            tmp["target"] = i.target
            tmp['time'] = time_str.split(" ")[-1]
            tmp["money"] = "%.2f" % (i.money)
            datas.append(tmp)

        data = {
            "code": 0,
            "data": datas
        }
        return JsonResponse(data)

# 以下 门店端API
class StoreActive(View):
    # 获取门店发起的活动 分页实现
    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        page_num = req.GET.get("page")
        num = req.GET.get("num")
        store = user.store_set.all()[0]
        actives = ActiveStoreMap.objects.filter(
            store_id=store.id,
        ).order_by("-create_time")
        paginator = Paginator(actives, num)

        page_data = []
        try:
            page = paginator.page(page_num)
            page_data = page.object_list
        except:
            data = {
                "code": 0,
                "data":[]
            }
            return JsonResponse(data)
        ac_data = []
        for i in page_data:
            tmp = model_to_dict(i.active)
            time_str = i.active.create_time.strftime("%Y年%m月%d日 %H:%M:%S")
            tmp["date"] = time_str.split(" ")[0]
            tmp['time'] = time_str.split(" ")[-1]
            tmp['create_time'] = time_str
            ac_data.append(tmp)
        ac_data = sorted(ac_data, key=lambda dic:dic["create_time"], reverse=True)
        data = {
            "code": 0,
            "data": ac_data
        }
        return JsonResponse(data)


# 获取门店活动余额
class StoreBalanceAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        store = user.store_set.all().first()
        data = {
            "code":0,
            "data":store.storeactivebalance
        }
        return JsonResponse(data)

# 门店红包发放记录
class StoreSendMoneyHistoryAPI(View):

    def get(self, req):
        user = ShangmiUser.objects.get(
            pk=int(user_cache.get(
                req.GET.get("token")
            )
            )
        )
        store = user.store_set.all().first()
        maps = store.activestoremap_set.all()
        actives = [i.active.id for i in maps]
        logs = UserActiveLog.objects.filter(active_id__in=actives)
        datas = []
        for i in logs:
            tmp = model_to_dict(i)
            time_str = i.create_time.strftime("%Y年%m月%d日 %H:%M:%S")
            tmp["date"] = time_str.split(" ")[0]

            tmp['time'] = time_str.split(" ")[-1]
            tmp["create_time"] = time_str
            tmp["type"] = i.get_type_display()
            tmp["status"] = i.get_status_display()
            tmp["active_name"] = i.active.name
            datas.append(tmp)
        ac_data = sorted(datas, key=lambda dic: dic["create_time"], reverse=True)
        data = {
            "code": 0,
            "data": ac_data
        }
        return JsonResponse(data)
#         获取时间 领取人 领取方式
def test(req):
    from io import BytesIO
    text = req.GET.get("text")
    text="赏米成功收款%s元" % str(text)
    res = get_voice(str(text))
    data = BytesIO(res)
    return HttpResponse(data.getvalue(), content_type="audio/m4a")

class BaoxianAPI(View):

    def post(self, req):
        # data = {
        #     "code": 0,
        #     "msg": "领取成功 积分已存至余额"
        # }
        # return JsonResponse(data)
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            req.POST.get("token")
        )))
        aid = req.POST.get("aid")
        params = req.POST
        active = Active.objects.get(pk=int(aid))

        if active.is_active == False:
            data = {
                "code": 1,
                "msg": "活动已经结束"
            }
            return JsonResponse(data)

        idcard = params.get("idcard")
        # obj = IDnumber()
        # res = obj.check(idcard)
        if len(idcard) == 18 or len(idcard) == 15:
            pass
        else:
            data = {
                "code": 1,
                "msg": "身份证无效"
            }
            return JsonResponse(data)
        # 判断年纪
        # age = res[1]
        # if age<25 or age>47:
        #     data = {
        #         "code": 1,
        #         "msg": "您的年纪不符合领取条件"
        #     }
        #     return JsonResponse(data)
        phone = params.get("phone")
        name = params.get("name")
        # 校验用户是否已经参与过
        is_join = UserActiveLog.objects.filter(
            user=user,
            active=active,
            status=1
        ).exists()
        if is_join:
            data = {
                "code":1,
                "msg": "您已经参与过了，可分享他人"
            }
            return JsonResponse(data)
        # 获取code 然后验证验证码
        code = params.get("code")
        cache_code = cache.get("baoxian"+phone)
        if cache_code and code == cache_code:
            pass
        else:
            data = {
                "code": 1,
                "msg": "验证码无效"
            }
            return JsonResponse(data)

        birth = ''
        sex = ''
        code = ''
        res = submit_one(name, phone, birth, sex, idcard, code)
#         判断是否是80 如果是 修改用户余额
        if res.get("error_code") == "80" or res.get("error_code") == "0":
            try:
                balance = Balance.objects.get(
                    user=user
                )
            except:
                balance = Balance.objects.create(
                    user=user
                )
            # 修改日志状态
            log = UserActiveLog.objects.create(
                user_id=user.id,
                active=active,
                integral=active.give_money,
                status=1,
                type="join"
            )
            active.complete_num += 1
            active.save()
            # log.status = 1
            # log.save()
            # 添加用户积分
            balance.money += active.give_money
            balance.save()
            # 保存用户信息
            user.phone = phone,
            user.idcard = idcard
            user.name = name
            user.save()
            data = {
                "code":0,
                "msg": "领取成功 积分已存至余额"
            }
            return JsonResponse(data)
        else:
            data = {
                "code": 1,
                "msg": res.get("error_msg")
            }
            return JsonResponse(data)

# 发送短信验证码
class SendCodeAPI(View):

    def get(self, req):
        phone = req.GET.get("phone")
        code = str(random.randrange(1000, 9999))
        params = "{\"code\":\"%s\"}" % code
        res = send_sms(phone, "赏米客户端", params)
        if res.get("Message") == "OK" and res.get("Code") == "OK":
            live_time = 60 * 5 #5分钟
            cache.set("baoxian"+phone, code, live_time)
            data = {
                "code": 0,
                "msg": "发送成功"
            }
        else:
            data = {
                "code": 1,
                "msg": res.get("Message")
            }
        return JsonResponse(data)

# 取消活动发布
class StoreCancleActive(View):

    def post(self, req):
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            req.POST.get("token")
        )))
        store = user.store_set.all()[0]
        actives = store.activestoremap_set.filter(
            active__is_active=True
        )
        if actives.exists():
            actives.update(is_active=False)
        data = {
            "code": 0,
            "msg": "已取消发布"
        }
        return JsonResponse(data)

class TiXianIndex(View):

    def get(self, req):
        data = {
            "code": 0,
            "data":{
                "target": "提现到",
                "weixin": "微信零钱",
                "hint": "提现金额需大于等于1元",
                "num_hint": "提现金额",
                "now": "本次可提现",
                "all": "全部提现",
                "input_hint":"输入金额超过零钱余额",
                "btn": "提现"
            }
        }
        return JsonResponse(data)


class CheckIdCardAPI(View):

    def get(self, req):
        # return JsonResponse({"code": 0})
        params = req.GET
        # token = params.get("token")
        # if user_cache.get(token) is None:
        #     return HttpResponseForbidden("权限不够")
        idcard = params.get("idcard")
        if len(idcard) == 18 or len(idcard) == 15:
            pass
        else:
            data = {
                "code": 1,
                "msg": "身份证位数不正确"
            }
            return JsonResponse(data=data)
        res = check_id(idcard)
        if res and len(res) != 3:
            data = {
                "code": 1,
                "msg": "这是无效的身份证"
            }
            return JsonResponse(data)
        else:
            return JsonResponse({"code": 0})
        # if res and len(res) == 3:
        #     city = res[-1].split(" ")[1]
        #     if city[-1] == "市":
        #         city = city[:-1]
        #     if city in city2 or city in citys:
        #         data = {
        #             "code": 0,
        #             "msg": "OK"
        #         }
        #         return JsonResponse(data)
        #     else:
        #         data = {
        #             "code": 1,
        #             "msg": "您的身份证所在地可能不能参与"
        #         }
        #         return JsonResponse(data)
        #
        # else:
        #     data = {
        #         "code": 1,
        #         "msg": "身份证无效, 请仔细核对"
        #     }
        #     return JsonResponse(data)

        # age = res[1]
        # if age<25 or age>47:
        #     data = {
        #         "code": 1,
        #         "msg": "您的年纪不符合领取条件"
        #     }
        #     return JsonResponse(data)