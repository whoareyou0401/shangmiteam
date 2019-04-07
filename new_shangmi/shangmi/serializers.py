from rest_framework import serializers
from .models import UserRecharge
class UserRechargeSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format="%Y年%m月%d日 %H:%M:%S")
    class Meta:
        model = UserRecharge
        fields = (
            "id", "money", "recharge_type", "create_time"
        )