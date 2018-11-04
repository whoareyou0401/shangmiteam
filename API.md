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

