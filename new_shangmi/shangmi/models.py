from django.db import models

# Create your models here.
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


class Balance(models.Model):
    money = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        verbose_name="余额"
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


class Store(models.Model):
    name = models.CharField(
        verbose_name="店铺名",
        max_length=40
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
    class Meta:
        verbose_name = "用户提现表"