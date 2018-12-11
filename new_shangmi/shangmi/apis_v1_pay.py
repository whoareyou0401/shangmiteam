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

user_cache = caches['user']
class OrderAPI(View):

    def post(self, req):
        user = ShangmiUser.objects.get(pk=int(user_cache.get(
            req.POST.get("token")
        )))
        use = req.POST.get("use")
        id = int(req.POST.get("id"))
        money = float(req.POST.get("money")) * 100

        need = money
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
            else:
                integral = user.balance.money
                # 用户积分清0
                user.balance.money = 0
                user.balance.save()
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
        # print('=------',rdict, '--------------')
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
                log.save()
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

# def store_get_money(req):
#
#     user = utils.request_user(req)
#     params = req.POST
#     store_id = int(params.get('store_id'))
#     identity = params.get('identity')
#
#     # 检查是否超过体现次数
#     now = datetime.datetime.now()
#     logs = ReflectLog.objects.filter(
#         user_id=user.id,
#         create_time__year=now.year,
#         create_time__month=now.month,
#         create_time__day=now.day
#     )
#     if logs.count() >= 2:
#         data = {
#             'code': 6,
#             'msg': "今日提现次数已达上限",
#             'data': ""
#         }
#         return JsonResponse(data)
#     money = float(req.POST.get("money"))
#     # 判断最大体现金额
#     if money > 10000:
#         data = {
#             'code': 6,
#             'msg': "单次提现金额不能超过一万元",
#             'data': ""
#         }
#         return JsonResponse(data)
#     # 查看当前金额
#     current_money = 0
#     if identity == 'boss':
#         current_money = utils.get_boss_money(store_id)
#     if identity == 'saler':
#         smap = StoreSalerMap.objects.get(
#             saler__user_id=user.id,
#             store_id=store_id)
#         current_money = utils.get_saler_money(store_id, smap.saler.id)
#
#
#     if current_money < money:
#         return JsonResponse({"code":5, "data":"金额过大"})
#     ip = req.META["REMOTE_ADDR"]
#     mchid = environ.get('MCHID')
#     pay_key = environ.get("PAY_KEY")
#     appid = environ.get('PAY_APPID')
#     log = ReflectLog.objects.create(
#         user=user,
#         money=money,
#
#     )
#     log.partner_trade_no = create_mch_billno(str(log.id).rjust(14).replace(" ", "0"))
#     log.save()
#
#     randuuid = uuid.uuid4()
#     nonce_str = str(randuuid).replace('-', '').upper()
#     partner_trade_no = log.partner_trade_no
#     data = {}
#     data["spbill_create_ip"] = ip
#     data['mch_appid'] = 'wxebd828458f8b2b38'
#     data['mchid'] = mchid
#     data['nonce_str'] = nonce_str
#     data['partner_trade_no'] = partner_trade_no
#     data['openid'] = user.openid
#     data['re_user_name'] = user.wx_name if user.wx_name else ''
#     data['amount'] = money * 100
#     data['check_name'] = 'NO_CHECK'
#     data['desc'] = "提现"
#     data['sign'] = sign(data, pay_key)
#     data_template = """
#                     <xml>
#                         <mch_appid>{mch_appid}</mch_appid>
#                         <mchid>{mchid}</mchid>
#                         <nonce_str>{nonce_str}</nonce_str>
#                         <partner_trade_no>{partner_trade_no}</partner_trade_no>
#                         <openid>{openid}</openid>
#                         <check_name>{check_name}</check_name>
#                         <re_user_name>{re_user_name}</re_user_name>
#                         <amount>{amount}</amount>
#                         <desc>{desc}</desc>
#                         <spbill_create_ip>{spbill_create_ip}</spbill_create_ip>
#                         <sign>{sign}</sign>
#                     </xml>""".format(**data)
#
#     headers = {'Content-Type': 'application/xml'}
#     raw = requests.post(settings.IMPORTTANT_URL,
#                         data=data_template,
#                         headers=headers,
#                         cert=(settings.WEIXIN_PAY_CERT_PATH, settings.WEIXIN_PAY_CERT_KEY_PATH))
#     rdict = xml_response_to_dict(raw)
#     data = {}
#     if rdict.get("return_code") == "SUCCESS" and rdict.get("result_code") == "SUCCESS":
#         payment_no = rdict.get("payment_no")
#         log.payment_no = payment_no
#         log.is_ok = True
#         log.save()
#         data["code"] = 0
#         data["data"] = {"current_money": current_money-money}
#     else:
#         data = {
#             "data":{"current_money": current_money-money},
#             "code":0
#         }
#     return JsonResponse(data)
