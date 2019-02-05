# -*- coding: utf-8 -*-
import uuid

from django.conf import settings
from django.core.cache import caches, cache
from itsdangerous import URLSafeTimedSerializer as utsr

from django.http import QueryDict, JsonResponse
import base64
import requests
import six

# from new_shangmi.new_shangmi.settings import SMS_ACCESS_KEY_ID, SMS_ACCESS_KEY_SECRET
# settings
from django.conf import settings
from .models import *
import socket
import hashlib
import xmltodict
import json
import os
from django.core.mail import send_mail
from math import radians, cos, sin, asin, sqrt
from aip import AipSpeech

from .aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
from .aliyunsdkdysmsapi.request.v20170525 import QuerySendDetailsRequest
from aliyunsdkcore.client import AcsClient
import uuid
from aliyunsdkcore.profile import region_provider
from aliyunsdkcore.http import method_type as MT
from aliyunsdkcore.http import format_type as FT
user_cache = caches['user']

def get_voice(text):
    APP_ID = '15347392'
    API_KEY = 'fkKUIHIFeqNSlSBjHpyNe47u'
    SECRET_KEY = 'QC7dRS1c4gmMi1wZd2lPk8zHOjkPGcQq'

    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
    result = client.synthesis(text=text, options={'vol': 8})
    return result

def send_sms(phone_numbers, sign_name, template_param=None):
    acs_client = AcsClient(
        settings.SMS_ACCESS_KEY_ID,
        settings.SMS_ACCESS_KEY_SECRET,
        settings.REGION
    )
    region_provider.add_endpoint(
        settings.PRODUCT_NAME,
        settings.REGION,
        settings.DOMAIN
    )
    smsRequest = SendSmsRequest.SendSmsRequest()
    # 申请的短信模板编码,必填
    smsRequest.set_TemplateCode(settings.SMS_TEMPLATE_ID)

    # 短信模板变量参数
    if template_param is not None:
        smsRequest.set_TemplateParam(template_param)

    # 设置业务请求流水号，必填。
    business_id = uuid.uuid1()
    smsRequest.set_OutId(business_id)

    # 短信签名
    smsRequest.set_SignName(sign_name)

    # 数据提交方式
    # smsRequest.set_method(MT.POST)

    # 数据提交格式
    # smsRequest.set_accept_format(FT.JSON)

    # 短信发送的号码列表，必填。
    smsRequest.set_PhoneNumbers(phone_numbers)

    # 调用短信发送接口，返回json
    smsResponse = acs_client.do_action_with_exception(smsRequest)

    # TODO 业务处理

    return json.loads(smsResponse.decode())




# 九堡30.307717 120.266319
def haversine(lon1, lat1, lon2, lat2):  # 经度1，纬度1，经度2，纬度2 （十进制度数）
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # 将十进制度数转化为弧度
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine公式
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # 地球平均半径，单位为公里
    return round(c * r, 2)


def req_user(request):
    if request.method == "GET":
        token = request.GET.get('token')
    else:
        params = QueryDict(request.body)
        token = params.get('token')
    uid = user_cache.get("token")
    if uid:
        user = ShangmiUser.objects.get(pk=int(uid))
    else:
        return None
    return user

def send_my_normal_mail(msg_str):
    sub = "赏米"
    recievers = [
        "wangjia8621@sina.com",
        "liuda@1000phone.com"
    ]

    send_mail(
        sub,
        msg_str,
        settings.DEFAULT_FROM_EMAIL,
        recievers
    )
    return "ok"

def send_mymail(store, active_name):
    sub = "赏米"
    recievers = [
        "wangjia8621@sina.com",
        "liuda@1000phone.com"
    ]
    msg = "{store_name}的老板{boss}申请了一个新的活动{name}，快去审核吧".format(
        boss=store.boss.nick_name,
        name=active_name,
        store_name=store.name
    )
    send_mail(
        sub,
        msg,
        settings.DEFAULT_FROM_EMAIL,
        recievers
    )
    return "ok"

def send_my_store_mail(store, active_name):
    sub = "赏米"
    recievers = [
        "wangjia8621@sina.com",
        "liuda@1000phone.com"
    ]
    msg = "{store_name}的老板{boss}申请了一个新的活动{name}，余额不足，请及时联系店老板".format(
        boss=store.boss.nick_name,
        name=active_name,
        store_name=store.name
    )
    send_mail(
        sub,
        msg,
        settings.DEFAULT_FROM_EMAIL,
        recievers
    )
    return "ok"

from functools import wraps


def login_req(func):
    @wraps
    def inner(request, *args, **kwargs):
        print(request)
        user = req_user(request)
        if not user:
            return JsonResponse({})
        request.user = user
        res = func(request, *args, **kwargs)
        return res

    return inner


def sign(params, sign_key="6C57AB91A1308E26B797F4CD382AC79D"):
    method = params.get('method')
    params = [(u'%s' % key, u'%s' % val) for key, val in params.iteritems() if val]
    params = sorted(params)
    sorted_params_string = ''.join(''.join(pair) for pair in params)
    sign_str = method + sorted_params_string + sign_key,
    md5 = hashlib.md5()
    md5.update(sign_str[0])
    return md5.hexdigest().upper()


def get_local_ip():
    myname = socket.getfqdn(socket.gethostname())
    myaddr = socket.gethostbyname(myname)
    return myaddr


def pay_sign(params, sign_key):
    params = [(u'%s' % key, u'%s' % val) for key, val in params.iteritems() if val]
    sorted_params_string = '&'.join('='.join(pair) for pair in sorted(params))
    sign = '{}&key={}'.format(sorted_params_string.encode('utf-8'), sign_key)
    md5 = hashlib.md5()
    md5.update(sign)
    return md5.hexdigest().upper()


def xml_response_to_dict(rep):
    d = xmltodict.parse(rep.content)
    return dict(d['response'])


def get_phone_area(phone):
    url = 'http://i.ataohao.com/api/hw?cmd=80100031&param=%3Cnumber%3E{phone}%3C/number%3E%3Ctype%3E1%3C/type%3E'.format(
        phone=phone)
    res = requests.get(url=url)
    data = xml_response_to_dict(res)
    return data.get('locInfo')


def get_url(url, params):
    p = ''
    for key in params:
        p += "&" + key + "=" + str(params.get(key))
    sign_str = sign(params)
    p = url + '?sign=' + sign_str + p
    return p


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def confirm_validate_token(token, expiration=settings.SMALL_WEIXIN_TOKEN_VALID_TIME):
    serializer = utsr(settings.SECRET_KEY)
    salt = base64.encodebytes(settings.SECRET_KEY)
    return serializer.loads(token, salt=salt, max_age=expiration)


def generate_validate_token(openid):
    serializer = utsr(settings.SECRET_KEY)
    salt = base64.encodebytes(settings.SECRET_KEY)
    return serializer.dumps(openid, salt)


def request_user(request):
    if request.method == "GET":
        token = request.GET.get('token')
    else:
        params = QueryDict(request.body)
        token = params.get('token')
    openid = confirm_validate_token(token)
    user = models.User.objects.get(openid=openid)
    return user


def distance_to_location(current_lng, current_lat, radius):
    add_lat = radius / settings.CM_DISCOVER_STORE_LAT_TO_DISTANCE
    add_lng = radius / settings.CM_DISCOVER_STORE_LNG_TO_DISTANCE
    radius_lat_location = add_lat / 3600
    radius_lng_location = add_lng / 3600
    start_lat = current_lat - radius_lat_location
    end_lat = current_lat + radius_lat_location
    start_lng = current_lng - radius_lng_location
    end_lng = current_lng + radius_lng_location
    return [start_lng, end_lng, start_lat, end_lat]


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def get_unique_name():
    # 获得一个uuid字符串
    uuid_val = uuid.uuid4()
    # 将uuid转成字符串
    uuid_str = str(uuid_val).encode("utf-8")
    # 获得一个md5
    md5 = hashlib.md5()
    # 将uuid字符串 做摘要
    md5.update(uuid_str)
    # 返回32位16进制结果
    return md5.hexdigest()

def get_access_token():
    appid = "wxebd828458f8b2b38"  # os.environ.get("SHANGMI_GZ_APPID")
    secret = "a40cb9c5ecb1f4f5c0f31b75829fed03"
    params = {'appid': appid,
              'secret': secret,
              'grant_type': 'client_credential'}
    url = 'https://api.weixin.qq.com/cgi-bin/token'
    response = requests.get(url, params=params)
    res = json.loads(response.content.decode())
    return res.get('access_token')


def get_access_token_function(appid, secret):
    TEST_APP_ACCESS_TOKEN = 'test_app_access_token1'
    access_token = cache.get(TEST_APP_ACCESS_TOKEN)
    if access_token is None:
        response = requests.get(
            url="https://api.weixin.qq.com/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": appid,
                "secret": secret,
            }
        )
        response_json = response.json()
        access_token = response_json['access_token']
        TIME_OUT = 60 * 60
        cache.set(
            TEST_APP_ACCESS_TOKEN,
            access_token,
            TIME_OUT)
    return access_token


def send_template_msg(openid, log, form_id):
    data = {
        "touser": openid,
        "template_id": "NmA5bKqWdiy1874A_fd3lhNm30-cKuPXGRtwnOIy-hg",
        "page": "pages/detail/detail",
        "form_id": form_id,
        "data": {
            "keyword1": {
                "value": "%.2f" % ((log.money + log.integral) / 100)
            },
            "keyword2": {
                "value": "%.2f" % (log.integral / 100)
            },
            "keyword3": {
                "value": "%.2f" % (log.money / 100)
            },
            "keyword4": {
                "value": log.create_time.strftime("%Y年%m月%d日 %H:%M:%S")
            },
            "keyword5": {
                "value": log.store.boss.nick_name
            }
        }
    }

    # appid = "wxebd828458f8b2b38"  # os.environ.get("SHANGMI_GZ_APPID")
    # secret = "a40cb9c5ecb1f4f5c0f31b75829fed03"  # os.environ.get("SHANGMI_GZ_SCERET")
    appid = "wx8b50ab8fa813a49e"  # os.environ.get("SHANGMI_GZ_APPID")
    secret = "b32f63c36ea123710173c4c9d4b15e8b"  # os.e
    token = get_access_token_function(appid, secret)
    # token = get_access_token()
    url = settings.GET_MONEY_TEMPLTAE_URL + "?access_token=" + token
    retry = 0
    print(data)
    # 三次重试
    while retry < 3:
        response = requests.post(url, data=json.dumps(data))
        response_json = response.json()
        print(response_json)
        errcode = response_json.get('errcode')
        errmsg = response_json.get('errmsg')

        if errcode == 0 and errmsg == 'ok':
            break
        else:
            retry += 1
