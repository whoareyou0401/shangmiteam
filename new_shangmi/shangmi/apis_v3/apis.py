from django.core.cache import caches
from django.http import JsonResponse
from django.views import View

from shangmi.models import *

from .utils import submit_msg_to_xm
user_cache = caches['user']
cache = caches['default']

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

        # birth = ''
        # sex = ''
        # code = ''
        clint_ip = req.META.get("REMOTE_ADDR")
        # res = submit_one(name, phone, birth, sex, idcard, code)
        status, msg = submit_msg_to_xm(name, phone, clint_ip, idcard)
#         判断是否是80 如果是 修改用户余额
        if status:
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
                "msg": msg
            }
            return JsonResponse(data)