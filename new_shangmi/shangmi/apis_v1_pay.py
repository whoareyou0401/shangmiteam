import json
import uuid
import datetime
import requests
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from os import environ
from django.conf import settings
import pay_util
# from pay_util import *
# from shangmi import utils
# from .models import ReflectLog, StoreSalerMap

class pay_unifiedorder(View):
    params = QueryDict(request.body)

    def post(self, request):
        if request.META.has_key('HTTP_X_FORWARDED_FOR'):
            ip = request.META.get('HTTP_X_FORWARDED_FOR')
        else:
            ip = request.META.get('REMOTE_ADDR')
        if ip in getattr(settings, 'BLOCKED_IPS', []):
            return HttpResponseForbidden('<h1>Forbbidden</h1>')
        token = params.get('token')
        order_id = params.get('order_id')
        openid = pay_util.confirm_validate_token(token)
        sid = int(cache.get(openid))
        store = models.Store.objects.get(id=sid)
        if hasattr(store, 'cvsconfig'):
            config = store.cvsconfig
        else:
            raise Exception('No config')
        # user = User.objects.get(openid=openid)
        # helper = CartHelper(openid)
        # cart_items = helper.get()
        # amount = cart_items.get('amount')
        randuuid = uuid.uuid4()
        nonce_str = str(randuuid).replace('-', '')
        out_trade_no = pay_util.create_mch_billno(str(order_id))
        cache.set(out_trade_no, order_id, timeout=24 * 60 * 60)
        url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
        data = {}
        data['body'] = u'超便利'
        data['mch_id'] = config.mch_id
        data['nonce_str'] = nonce_str
        # data['device_info'] = 'WEB'
        data['total_fee'] = str(int(amount * 100))
        data['spbill_create_ip'] = ip
        # data['fee_type'] = 'CNY'
        data['openid'] = openid
        data['out_trade_no'] = out_trade_no
        data['notify_url'] = 'https://%s/api/v1.0/pay/notify' % (request.get_host())
        data['appid'] = config.appid
        data['trade_type'] = 'JSAPI'
        data['sign'] = pay_util.sign(data, config.pay_api_key)
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
        rdict = pay_util.xml_response_to_dict(raw)

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
            paySign = pay_util.sign(sign_data, config.pay_api_key)
            return_data['appId'] = rdict['appid']
            return_data['paySign'] = paySign
            return_data['nonceStr'] = nonce_str
            return_data['timeStamp'] = time_stamp
            return_data['package'] = 'prepay_id=%s' % rdict['prepay_id']
            return_data['signType'] = 'MD5'
            return {'data': return_data}
        else:
            return JsonResponse({'code': 1, 'data': u'支付失败'})

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
