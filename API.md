# 客户端API接口说明

## 1 活动列表API

url:"api/v1/shangmi/active"

请求方式：GET

请求参数：

​	无

返回参数

{

​	“fast”:[{字段说明见下表}]，   #选取的数据是is_fast=True

​	“unfast”: [{}]                              #选取的数据是is_fast=False

}

| 名字   | 类型     | 备注      |
| ---- | ------ | ------- |
| id   | int    | 活动id    |
| name | string | 活动名字    |
| icon | string | 活动logo  |
| desc | string | 活动的简短描述 |

## 2 消费者参加活动记录

url: "api/v1/shangmi/user_active_log"

请求方式：GET

参数：

​	token 用户的token

逻辑：

​	根据用户id搜索对应的数据，按照时间字段降序排列

返回数据：

```
UserActiveLog的全部字段数据
```