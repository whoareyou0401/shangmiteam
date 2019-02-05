from __future__ import unicode_literals
import json
import uuid
import datetime
import time
import requests
from django.core.cache import cache, caches
from django.http import HttpResponse, JsonResponse, QueryDict, HttpResponseForbidden
from django.views.generic import View
from os import environ
from django.conf import settings
from .pay_util import *
from .models import *
import xmltodict
from .utils import send_template_msg, send_my_normal_mail
import redis
user_cache = caches['user']
client = redis.StrictRedis(db=8)
class OrderAPI(View):

    def post(self, req):
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            req.POST.get("token")
        )))
        use = req.POST.get("use")
        id = int(req.POST.get("id"))
        money = float(req.POST.get("money")) * 100

        need = money
        store = Store.objects.get(id=id)
        if store.is_active == False:
            data = {
                "code": 2,
                "msg": "该店已经停止合作"
            }
            return JsonResponse(data)
        integral = 0
        status = 0
        if use == "true":
            need = money - float(user.balance.money)
            if need < 0:
                user.balance.money = float(user.balance.money) - money
                user.balance.save()
                is_success = 1
                integral = money
                status = 1
                store_balance = Balance.objects.get_or_create(
                    user=store.boss
                )[0]
                if store.is_receive:
                    data = {
                        "sid": store.id,
                        "money": "%.1f" % (money / 100)
                    }
                    client.publish("buy", json.dumps(data))
                # 店长余额等于 商户付的钱 加 客户使用的积分
                store_balance.money = float(store_balance.money) + money + money
                store_balance.save()
                need=0
            else:
                integral = user.balance.money
                # 用户积分清0
                user.balance.money = 0
                user.balance.save()
                # 给店老板加钱
                store_balance = Balance.objects.get_or_create(
                    user=store.boss
                )[0]
                # store_balance.money = store_balance.money + integral
                # store_balance.save()
                # 需要付钱
                is_success = 0
        elif use=="false":
            is_success = 0
        log = UserPayLog.objects.create(
            user=user,
            store_id=id,
            money=need,
            integral=integral,
            status=status
        )
        if is_success == 0:
            log.wx_pay_num = create_mch_billno(str(log.id))
        order_num = datetime.datetime.now().strftime("%Y%m%d%H%M") + str(log.id)
        log.order_num = order_num
        log.save()
        data = {
            "code": 0,
            "data": {
                "is_success": is_success,
                "need": need,
                "id": log.id
            }
        }
        return JsonResponse(data)

# 消费者支付接口
class pay_unifiedorder(View):


    def post(self, request):
        params = QueryDict(request.body)
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            ip = request.META.get('HTTP_X_FORWARDED_FOR')
        else:
            ip = request.META.get('REMOTE_ADDR')
        if ip in getattr(settings, 'BLOCKED_IPS', []):
            return HttpResponseForbidden('<h1>Forbbidden</h1>')
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            params.get("token")
        )))
        order_id = params.get('order_id')
        amount = params.get("need")
        log = UserPayLog.objects.get(id=order_id)
        randuuid = uuid.uuid4()
        nonce_str = str(randuuid).replace('-', '')
        out_trade_no = log.wx_pay_num
        # log.wx_pay_num = out_trade_no
        # log.save()
        url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
        data = {}
        data['body'] = 'ShangMi'.encode('utf-8')
        data['mch_id'] = settings.MCHID
        data['nonce_str'] = nonce_str
        # data['device_info'] = 'WEB'
        data['total_fee'] = str(int(amount))
        data['spbill_create_ip'] = ip
        # data['fee_type'] = 'CNY'
        data['openid'] = user.openid
        data['out_trade_no'] = out_trade_no
        # data['notify_url'] = 'http://sharemsg.cn:12348/shangmi/api/v1/pay/notify'
        data['notify_url'] = 'https://sharemsg.cn/shangmi/api/v1/pay/notify'
        data['appid'] = settings.PAY_APPID
        data['trade_type'] = 'JSAPI'
        data['sign'] = sign(data, settings.PAY_KEY)
        template = """
                    <xml>
                    <appid>{appid}</appid>
                    <body>{body}</body>
                    <mch_id>{mch_id}</mch_id>
                    <nonce_str>{nonce_str}</nonce_str>
                    <notify_url>{notify_url}</notify_url>
                    <openid>{openid}</openid>
                    <out_trade_no>{out_trade_no}</out_trade_no>
                    <spbill_create_ip>{spbill_create_ip}</spbill_create_ip>
                    <total_fee>{total_fee}</total_fee>
                    <trade_type>{trade_type}</trade_type>
                    <sign>{sign}</sign>
                    </xml>
                """
        content = template.format(**data)
        headers = {'Content-Type': 'application/xml'}
        raw = requests.post(url, data=content, headers=headers)
        rdict = xml_response_to_dict(raw)
        return_data = {}
        if rdict['return_code'] == 'SUCCESS' and rdict['result_code'] == 'SUCCESS':
            randuuid = uuid.uuid4()
            log.prepay_id = rdict['prepay_id']
            log.save()
            nonce_str = str(randuuid).replace('-', '')
            time_stamp = str(int(time.time()))
            sign_data = {}
            sign_data['appId'] = rdict['appid']
            sign_data['nonceStr'] = nonce_str
            sign_data['package'] = 'prepay_id=%s' % rdict['prepay_id']
            sign_data['signType'] = 'MD5'
            sign_data['timeStamp'] = time_stamp
            paySign = sign(sign_data, settings.PAY_KEY)
            return_data['appId'] = rdict['appid']
            return_data['paySign'] = paySign
            return_data['nonceStr'] = nonce_str
            return_data['timeStamp'] = time_stamp
            return_data['package'] = 'prepay_id=%s' % rdict['prepay_id']
            return_data['signType'] = 'MD5'
            return JsonResponse({'data': return_data, "code":0})
        else:
            return JsonResponse({'code': 1, 'data': u'支付失败'})
# 消费者消息回调接口
class PayNotifyAPI(View):

    def post(self, request):
        d = xmltodict.parse(request.body)
        resp = dict(d['xml'])
        return_code = resp.get('return_code')
        data = {}
        if return_code == 'SUCCESS':
            """
            todo 这里需要做签名校验
            """
            # order_id = cache.get()
            log = UserPayLog.objects.get(wx_pay_num=resp.get('out_trade_no'))
            # log.wx_pay_num = resp.get('out_trade_no')
            if resp.get('appid') == settings.PAY_APPID \
                    and resp.get('mch_id') == settings.MCHID \
                    and float(resp.get('total_fee')) == log.money:
                log.status = 1
                log.store.boss.balance.money = log.store.boss.balance.money + log.money  + log.integral + log.integral
                log.save()
                log.store.boss.balance.save()
                if log.store.is_receive:
                    data = {
                        "sid": log.store.id,
                        "money": round((log.money + log.integral) / 100, 1)
                    }
                    client.publish("buy", json.dumps(data))
                # send_template_msg(log.user.openid,log, log.prepay_id )
                data['return_code'] = 'SUCCESS'
                data['return_msg'] = 'OK'
            else:

                data['return_code'] = 'FAIL'
                data['return_msg'] = 'SIGNERROR'
        else:
            data['return_code'] = 'FAIL'
            data['return_msg'] = 'OK'
        template = """
        <xml>
            <return_code><![CDATA[{return_code}]]></return_code>
            <return_msg><![CDATA[{return_msg}]]></return_msg>
        </xml>
        """
        content = template.format(**data)
        return HttpResponse(content, content_type='application/xml')

# m门店提现
class StoreGetMoneyAPI(View):
    def post(self, req):
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            req.POST.get("token")
        )))
        params = req.POST
        # store = user.store_set.all()[0]
        money = float(params.get('money'))
        if money<1:
            data = {
                "code": 2,
                "data": "提现金额不能小于1元"
            }
        # 检查是否超过体现次数
        now = datetime.datetime.now()
        logs = GetMoneyLog.objects.filter(
            user_id=user.id,
            create_time__year=now.year,
            create_time__month=now.month,
            create_time__day=now.day,
            is_ok=True
        )
        if logs.count() >= 2:
            data = {
                'code': 6,
                'msg': "今日提现次数已达上限",
                'data': ""
            }
            return JsonResponse(data)

        # 判断最大体现金额
        if money > 10000:
            data = {
                'code': 6,
                'msg': "单次提现金额不能超过一万元",
                'data': ""
            }
            return JsonResponse(data)
        # 查看当前金额
        current_money = 0
        if user.balance.money < money * 100:
            data  = {
                "code": 2,
                "msg": "提现金额超过余额",
                "data":''
            }
            return JsonResponse(data)

        ip = req.META["REMOTE_ADDR"]
        mchid = environ.get('MCHID')
        pay_key = environ.get("PAY_KEY")
        appid = environ.get('PAY_STORE_GET_MONEY_APPID')
        log = GetMoneyLog.objects.create(
            user=user,
            money=money
        )
        log.partner_trade_no = create_mch_billno(str(log.id).rjust(14).replace(" ", "0"))
        log.save()

        randuuid = uuid.uuid4()
        nonce_str = str(randuuid).replace('-', '').upper()
        partner_trade_no = log.partner_trade_no
        data = {}
        data["spbill_create_ip"] = ip
        data['mch_appid'] = appid
        data['mchid'] = mchid
        data['nonce_str'] = nonce_str
        data['partner_trade_no'] = partner_trade_no
        data['openid'] = user.openid
        data['re_user_name'] = user.nick_name if user.nick_name else ''
        data['amount'] = str(int(money * 100))
        data['check_name'] = 'NO_CHECK'
        data['desc'] = "提现"
        data['sign'] = sign(data, pay_key)
        data['re_user_name'] = data['re_user_name'].encode("utf-8").decode("latin1")
        data['desc'] = data['desc'].encode("utf-8").decode("latin1")
        data_template = """
                        <xml>
                            <mch_appid>{mch_appid}</mch_appid>
                            <mchid>{mchid}</mchid>
                            <nonce_str>{nonce_str}</nonce_str>
                            <partner_trade_no>{partner_trade_no}</partner_trade_no>
                            <openid>{openid}</openid>
                            <check_name>{check_name}</check_name>
                            <re_user_name>{re_user_name}</re_user_name>
                            <amount>{amount}</amount>
                            <desc>{desc}</desc>
                            <spbill_create_ip>{spbill_create_ip}</spbill_create_ip>
                            <sign>{sign}</sign>
                        </xml>""".format(**data)

        headers = {'Content-Type': 'application/xml'}
        raw = requests.post(settings.IMPORTTANT_URL,
                            data=data_template,
                            headers=headers,
                            cert=(settings.WEIXIN_PAY_CERT_PATH, settings.WEIXIN_PAY_CERT_KEY_PATH))
        rdict = xml_response_to_dict(raw)
        data = {}
        if rdict.get("return_code") == "SUCCESS" and rdict.get("result_code") == "SUCCESS":
            payment_no = rdict.get("payment_no")
            log.payment_no = payment_no
            log.is_ok = True
            log.save()
            user.balance.money = float(user.balance.money) - money * 100
            user.balance.save()
            data["code"] = 0
            data["data"] = {"current_money": user.balance.money}
        else:
            msg = "门店客户提现 用户id：%s支付问题%s" % (str(user.id), rdict.get("err_code_des"))
            send_my_normal_mail(msg)
            data = {
                "data":{"current_money": user.balance.money},
                "msg":"您今日不可提现了",
                "code":1
            }
        return JsonResponse(data)

# 用户提现
class UserGetMoneyAPI(View):
    def post(self, req):
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            req.POST.get("token")
        )))
        # if user.id not in [1,3,4]:
        #     data = {
        #         "code": 2,
        #         "msg": "暂时对您不开放"
        #     }
        #     return JsonResponse(data)
        params = req.POST
        # store = user.store_set.all()[0]
        money = float(params.get('money'))
        if money<1:
            data = {
                "code": 2,
                "msg": "提现金额不能小于1元"
            }
            return JsonResponse(data)
        # 检查是否超过体现次数
        now = datetime.datetime.now()
        logs = GetMoneyLog.objects.filter(
            user_id=user.id,
            create_time__year=now.year,
            create_time__month=now.month,
            create_time__day=now.day,
            is_ok=True
        )
        if logs.count() >= 2:
            data = {
                'code': 6,
                'msg': "今日提现次数已达上限",
                'data': ""
            }
            return JsonResponse(data)

        # 判断最大体现金额
        if money > 10000:
            data = {
                'code': 6,
                'msg': "单次提现金额不能超过一万元",
                'data': ""
            }
            return JsonResponse(data)
        # 查看当前金额
        current_money = 0
        if user.balance.money < money * 100:
            data  = {
                "code": 2,
                "msg": "提现金额超过余额",
                "data":''
            }
            return JsonResponse(data)

        ip = req.META["REMOTE_ADDR"]
        mchid = environ.get('MCHID')
        pay_key = environ.get("PAY_KEY")
        appid = environ.get('PAY_USER_GET_MONEY_APPID')
        log = GetMoneyLog.objects.create(
            user=user,
            money=money
        )
        log.partner_trade_no = create_mch_billno(str(log.id).rjust(14).replace(" ", "0"))
        log.save()

        randuuid = uuid.uuid4()
        nonce_str = str(randuuid).replace('-', '').upper()
        partner_trade_no = log.partner_trade_no
        data = {}
        data["spbill_create_ip"] = ip
        data['mch_appid'] = appid
        data['mchid'] = mchid
        data['nonce_str'] = nonce_str
        data['partner_trade_no'] = partner_trade_no
        data['openid'] = user.openid
        data['re_user_name'] = user.nick_name if user.nick_name else ''
        data['amount'] = str(int(money * 100))
        data['check_name'] = 'NO_CHECK'
        data['desc'] = "提现"
        data['sign'] = sign(data, pay_key)
        data['re_user_name'] = data['re_user_name'].encode("utf-8").decode("latin1")
        data['desc'] = data['desc'].encode("utf-8").decode("latin1")
        data_template = """
                        <xml>
                            <mch_appid>{mch_appid}</mch_appid>
                            <mchid>{mchid}</mchid>
                            <nonce_str>{nonce_str}</nonce_str>
                            <partner_trade_no>{partner_trade_no}</partner_trade_no>
                            <openid>{openid}</openid>
                            <check_name>{check_name}</check_name>
                            <re_user_name>{re_user_name}</re_user_name>
                            <amount>{amount}</amount>
                            <desc>{desc}</desc>
                            <spbill_create_ip>{spbill_create_ip}</spbill_create_ip>
                            <sign>{sign}</sign>
                        </xml>""".format(**data)

        headers = {'Content-Type': 'application/xml'}
        raw = requests.post(settings.IMPORTTANT_URL,
                            data=data_template,
                            headers=headers,
                            cert=(settings.WEIXIN_PAY_CERT_PATH, settings.WEIXIN_PAY_CERT_KEY_PATH))
        rdict = xml_response_to_dict(raw)
        data = {}

        if rdict.get("return_code") == "SUCCESS" and rdict.get("result_code") == "SUCCESS":
            payment_no = rdict.get("payment_no")
            log.payment_no = payment_no
            log.is_ok = True
            log.save()
            user.balance.money = float(user.balance.money) - money * 100
            user.balance.save()
            data["code"] = 0
            data["msg"] = "已提现至微信零钱"
            data["data"] = {"current_money": current_money-money}
        elif rdict.get("return_code") == "SUCCESS" and rdict.get("err_code") == "SENDNUM_LIMIT":
            data = {
                "msg": "提现次数过多",
                "code": 1
            }
        else:
            msg = "客户提现 用户id：%s支付问题%s"%(str(user.id),rdict.get("err_code_des"))
            send_my_normal_mail(msg)
            data = {
                "msg":"今日已不可提现",
                "code":1
            }
        return JsonResponse(data)

# 门店充值API
class StoreRechargeAPI(View):


    def post(self, request):
        params = QueryDict(request.body)
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            ip = request.META.get('HTTP_X_FORWARDED_FOR')
        else:
            ip = request.META.get('REMOTE_ADDR')
        if ip in getattr(settings, 'BLOCKED_IPS', []):
            return HttpResponseForbidden('<h1>Forbbidden</h1>')
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            params.get("token")
        )))
        # order_id = params.get('order_id')
        amount = float(params.get("money"))
        log = UserRecharge.objects.get_or_create(
            user=user,
            money=amount,
            is_ok=False
        )[0]
        randuuid = uuid.uuid4()
        nonce_str = str(randuuid).replace('-', '')
        out_trade_no = create_mch_billno(str(log.id))
        log.wx_pay_num = out_trade_no
        log.save()
        url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
        data = {}
        data['body'] = '充值'
        data['mch_id'] = settings.MCHID
        data['nonce_str'] = nonce_str
        # data['device_info'] = 'WEB'
        data['total_fee'] = str(int(amount * 100))
        data['spbill_create_ip'] = ip
        # data['fee_type'] = 'CNY'
        data['openid'] = user.openid
        data['out_trade_no'] = out_trade_no
        # data['notify_url'] = 'http://sharemsg.cn:12348/shangmi/api/v1/pay/store/notify'
        data['notify_url'] = 'https://sharemsg.cn/shangmi/api/v1/pay/store/notify'
        data['appid'] = environ.get('PAY_STORE_GET_MONEY_APPID')
        data['trade_type'] = 'JSAPI'
        data['sign'] = sign(data, settings.PAY_KEY)
        data['body'] = data['body'].encode("utf-8").decode("latin1")
        template = """
                    <xml>
                    <appid>{appid}</appid>
                    <body>{body}</body>
                    <mch_id>{mch_id}</mch_id>
                    <nonce_str>{nonce_str}</nonce_str>
                    <notify_url>{notify_url}</notify_url>
                    <openid>{openid}</openid>
                    <out_trade_no>{out_trade_no}</out_trade_no>
                    <spbill_create_ip>{spbill_create_ip}</spbill_create_ip>
                    <total_fee>{total_fee}</total_fee>
                    <trade_type>{trade_type}</trade_type>
                    <sign>{sign}</sign>
                    </xml>
                """
        content = template.format(**data)
        headers = {'Content-Type': 'application/xml'}
        raw = requests.post(url, data=content, headers=headers)
        rdict = xml_response_to_dict(raw)
        return_data = {}
        if rdict['return_code'] == 'SUCCESS' and rdict['result_code'] == 'SUCCESS':
            randuuid = uuid.uuid4()
            nonce_str = str(randuuid).replace('-', '')
            time_stamp = str(int(time.time()))
            sign_data = {}
            sign_data['appId'] = rdict['appid']
            sign_data['nonceStr'] = nonce_str
            sign_data['package'] = 'prepay_id=%s' % rdict['prepay_id']
            sign_data['signType'] = 'MD5'
            sign_data['timeStamp'] = time_stamp
            paySign = sign(sign_data, settings.PAY_KEY)
            return_data['appId'] = rdict['appid']
            return_data['paySign'] = paySign
            return_data['nonceStr'] = nonce_str
            return_data['timeStamp'] = time_stamp
            return_data['package'] = 'prepay_id=%s' % rdict['prepay_id']
            return_data['signType'] = 'MD5'
            return JsonResponse({'data': return_data, "code":0})
        else:
            return JsonResponse({'code': 1, 'data': u'支付失败'})

# 门店支付回调接口
class StorePayNotifyAPI(View):

    def post(self, request):
        d = xmltodict.parse(request.body)
        resp = dict(d['xml'])
        return_code = resp.get('return_code')
        data = {}
        if return_code == 'SUCCESS':
            """
            todo 这里需要做签名校验
            """
            # order_id = cache.get()
            log = UserRecharge.objects.get(wx_pay_num=resp.get('out_trade_no'))
            # log.wx_pay_num = resp.get('out_trade_no')



            if resp.get('appid') == environ.get('PAY_STORE_GET_MONEY_APPID') \
                    and resp.get('mch_id') == settings.MCHID \
                    and float(resp.get('total_fee')) == log.money * 100:
                log.is_ok = True
                log.save()
                try:
                    balance = Balance.objects.get(
                        user_id=log.user.id
                    )
                except:
                    balance = Balance.objects.create(
                        user_id=log.user.id
                    )
                balance.money += log.money * 100
                balance.save()
                # 门店活动
                # store = log.user.store_set.all()[0]
                # balance = StoreActiveBalance.objects.get_or_create(
                #     store=store
                # )[0]
                # balance.balance += log.money * 100
                # balance.save()
                # log.user.store_set.all()[0].boss.balance.save()
                data['return_code'] = 'SUCCESS'
                data['return_msg'] = 'OK'
            else:

                data['return_code'] = 'FAIL'
                data['return_msg'] = 'SIGNERROR'
        else:
            data['return_code'] = 'FAIL'
            data['return_msg'] = 'OK'
        template = """
        <xml>
            <return_code><![CDATA[{return_code}]]></return_code>
            <return_msg><![CDATA[{return_msg}]]></return_msg>
        </xml>
        """
        content = template.format(**data)

        return HttpResponse(content, content_type='application/xml')
