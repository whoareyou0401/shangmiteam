from django.db import models
from django.views import View

from .choices import *
# Create your models here.


ACTIVE_STATUS = (
    (0, "审核中"),
    (1, "审核通过"),
    (2, "审核失败")
)

class ShangmiUser(models.Model):
    openid = models.CharField(
        max_length=255,
        verbose_name="openid"
    )
    create_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    nick_name = models.CharField(
        verbose_name="昵称",
        null=True,
        max_length=30
    )
    source = models.CharField(
        max_length=30,
        verbose_name="用户来源"
    )
    icon = models.CharField(
        max_length=255,
        null=True
    )
    union_id = models.CharField(
        max_length=255,
        null=True,
        verbose_name="联合主键"
    )
    gz_openid = models.CharField(
        max_length=255,
        null=True,
        verbose_name="公众号openid"
    )
    lat = models.DecimalField(
        decimal_places=15,
        max_digits=30,
        null=True,
        verbose_name="纬度"
    )
    lng = models.DecimalField(
        decimal_places=15,
        max_digits=30,
        null=True,
        verbose_name="经度"
    )
    def __str__(self):
        return self.nick_name
    class Meta:
        verbose_name="用户数据"

class Balance(models.Model):
    money = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        verbose_name="余额",
        default=0
    )
    user = models.OneToOneField(
        ShangmiUser,
        verbose_name="用户"
    )
    update_time = models.DateTimeField(
        auto_now=True,
        verbose_name="用户余额更新时间"
    )
    class Meta:
        verbose_name = "余额积分表"


class Advertise(models.Model):
    name = models.CharField(
        verbose_name="海报名字",
        max_length=50
    )
    icon = models.CharField(
        max_length=255,
        verbose_name="海报封面"
    )
    # affect_time = models.DateField(
    #     verbose_name="截止日期",
    #     null=True
    # )
    is_used = models.BooleanField(
        default=True
    )
    class Meta:
        verbose_name = "海报"


class Store(models.Model):
    name = models.CharField(
        verbose_name="店铺名",
        max_length=40
    )
    address = models.CharField(
        verbose_name="地址",
        max_length=255,
        null=True
    )
    boss = models.ForeignKey(
        ShangmiUser,
        verbose_name="店老板"
    )
    create_time = models.DateTimeField(
        verbose_name="创建时间",
        auto_now_add=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否可用"
    )
    boss_phone = models.CharField(
        max_length=15,
        null=True,
        verbose_name="授权手机号"
    )
    notice = models.BooleanField(
        default=True,
        verbose_name="是否接收通知"
    )
    def __str__(self):
        return self.name
    class Meta:
        verbose_name="门店"

class GetMoneyLog(models.Model):
    user = models.ForeignKey(
        ShangmiUser,
        verbose_name="用户"
    )
    money = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        verbose_name="金额"
    )
    create_time = models.DateTimeField(
        verbose_name="创建时间",
        auto_now_add=True
    )
    partner_trade_no = models.CharField(
        max_length=255,
        null=True,
        verbose_name="下单号"
    )
    is_ok = models.BooleanField(
        default=False
    )
    payment_no = models.CharField(
        max_length=255,
        null=True
    )
    class Meta:
        verbose_name = "用户提现表"


class Active(models.Model):
    name = models.CharField(
        max_length=40,
        verbose_name="活动名字"
    )
    icon = models.CharField(
        max_length=255,
        verbose_name="海报封面"
    )
    desc = models.TextField(

        verbose_name="活动描述"
    )
    rule = models.CharField(
        max_length=255,
        verbose_name="活动规则",
        null=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否活跃"
    )
    create_time = models.DateTimeField(
        verbose_name="创建时间",
        auto_now_add=True
    )
    give_money = models.IntegerField(
        verbose_name="活动给予积分"
    )
    share_give_money = models.IntegerField(
        verbose_name="分享成功所得积分",
        null=True
    )
    is_fast = models.BooleanField(
        default=True,
        verbose_name="是否快速"
    )
    complete_num = models.IntegerField(
        default=0,
        verbose_name="完成量"
    )
    need_num = models.IntegerField(
        default=0,
        verbose_name="活动总量"
    )
    lat = models.DecimalField(
        decimal_places=15,
        max_digits=30,
        null=True,
        verbose_name="纬度"
    )
    lng = models.DecimalField(
        decimal_places=15,
        max_digits=30,
        null=True,
        verbose_name="经度"
    )
    range = models.FloatField(
        verbose_name="活动允许范围km",
        default=3
    )
    detail_url = models.CharField(
        max_length=255,
        null=True,
        verbose_name="详情页跳转"
    )
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "活动表"


class ActiveStoreMap(models.Model):
    active = models.ForeignKey(
        Active,
        verbose_name="活动"
    )
    store = models.ForeignKey(
        Store,
        verbose_name="门店"
    )
    create_time = models.DateTimeField(
        verbose_name="创建时间",
        auto_now_add=True
    )
    class Meta:
        verbose_name = "活动与门店关系表"
        unique_together = ['store', 'active'] #联合约束


class UserPayLog(models.Model):
    user = models.ForeignKey(
        ShangmiUser,
        verbose_name="普通用户"
    )
    store = models.ForeignKey(
        Store,
        verbose_name="门店"
    )
    money = models.IntegerField(
        verbose_name="差价钱数",
        null=True
    )
    integral = models.IntegerField(
        verbose_name="使用的积分数",
        null=True
    )
    order_num = models.CharField(
        max_length=255,
        verbose_name="咱们自己的订单编号",
        null=True
    )
    wx_pay_num = models.CharField(
        max_length=255,
        verbose_name="微信支付订单号"
    )
    create_time = models.DateTimeField(
        verbose_name="创建时间",
        auto_now_add=True
    )
    status = models.IntegerField(
        choices=PAY_STATUS,
        verbose_name="支付状态",
        default=0
    )
    prepay_id = models.CharField(
        max_length=255,
        null=True
    )
    class Meta:
        verbose_name = "用户付款表"
        index_together = ["user", "store"]


class UserActiveLog(models.Model):
    INTEGRAL_TYPE = (
        ("join", "直接参加"),
        ("share", "分享获得")
    )
    user = models.ForeignKey(
        ShangmiUser
    )
    active = models.ForeignKey(
        Active
    )
    integral = models.IntegerField(
        verbose_name="当时所获积分"
    )
    create_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="参加时间"
    )
    type = models.CharField(
        max_length=10,
        choices=INTEGRAL_TYPE,
        verbose_name="奖励来源"
    )
    status = models.IntegerField(
        default=0,
        verbose_name="审核状态",
        choices=ACTIVE_STATUS
    )
    class Meta:
        verbose_name = "用户获取积分记录表"

class UserRecharge(models.Model):

    user = models.ForeignKey(
        ShangmiUser,
        verbose_name="用户"
    )
    money = models.FloatField(
        verbose_name="充值金额"
    )
    create_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )
    is_ok = models.BooleanField(
        default=False,
        verbose_name="充值状态"
    )
    wx_pay_num = models.CharField(
        max_length=255,
        verbose_name="微信支付订单号"
    )
    class Meta:
        verbose_name="门店用户充值"

class StoreActiveBalance(models.Model):
    store = models.OneToOneField(
        Store,
        verbose_name="门店"
    )

    balance = models.FloatField(
        default=0,
        verbose_name="活动金余额"
    )
    update_time = models.DateTimeField(
        auto_now=True,
        verbose_name="参加时间"
    )


