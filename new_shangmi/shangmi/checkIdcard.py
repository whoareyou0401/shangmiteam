from datetime import date


class IDnumber:
    '''身份证号码类'''
    # 类属性 IDnumber.address_codes 单元包含了身份证前6位的行政区划代码。
    address_codes = {
        '110000': '北京市', # 此后省略了很多，字典具体内容可到我的资源页进行下载。
        '810000': '湾仔区',
        '810000': '中西区',
        }
    # 类属性 IDnumber.provinces 单元包含了省级行政区划代码。
    provinces = {
        '11': '北京市',
        '12': '天津市',
        '13': '河北省',
        '14': '山西省',
        '15': '内蒙古自治区',
        '21': '辽宁省',
        '22': '吉林省',
        '23': '黑龙江省',
        '31': '上海市',
        '32': '江苏省',
        '33': '浙江省',
        '34': '安徽省',
        '35': '福建省',
        '36': '江西省',
        '37': '山东省',
        '41': '河南省',
        '42': '湖北省',
        '43': '湖南省',
        '44': '广东省',
        '45': '广西省',
        '46': '海南省',
        '50': '重庆市',
        '51': '四川省',
        '52': '贵州省',
        '53': '云南省',
        '54': '西藏自治区',
        '61': '陕西省',
        '62': '甘肃省',
        '63': '青海省',
        '64': '宁夏回族自治区',
        '65': '新疆维吾尔族自治区',
        '71': '台湾省',
        '81': '香港特别行政区',
    }
    # 类属性 IDnumber.weights 列表储存乘法权重
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    # 类属性 IDnumber.mod_codes 单元储存了余数和正确校验码的对应关系
    mod_codes = {
        '0': '1', '1': '0', '2': 'X', '3': '9', '4': '8', '5': '7',
        '6': '6', '7': '5', '8': '4', '9': '3', '10': '2',
    }

    def _int_(self, flag):
        self.flag = True  # 判断输入是否合法的标志

    def number_test(self, id_num):
        """判断一个字符串是否全由数字组成"""
        self.id_num = id_num
        try:
            int(self.id_num)
        except ValueError:
            return False
        else:
            return True

    def judge_id_num(self):
        """判断输入是否是合法的身份证号码格式"""
        if len(self.id_num) != 18:
            return False
        elif self.number_test(self.id_num[0:18]):
            return True
        elif self.number_test(self.id_num[0:17]):
            if self.id_num[17:18] is 'X' or self.id_num[17:18] is 'x':
                return True
            else:
                return False
        else:
            return False

    def handle_id_num(self):
        """提取身份证有关信息，返回 True 表示内容提取无误"""
        # 6位地址码和籍贯
        self.addr_code = self.id_num[0:6]
        self.province = self.id_num[0:2]
        self.native_place = ''

        for key, value in IDnumber.provinces.items():
            if key == self.province:
                self.native_place += value
                break

        for key, value in IDnumber.address_codes.items():
            if key == self.addr_code:
                self.native_place += value
                break

        if self.native_place is '':
            return False
        else:
            # 6位出生日期
            self.bir_date = self.id_num[6:14]
            # 出生年、当前年
            self.bir_year = self.id_num[6:10]
            current_year = date.today().strftime("%Y")
            year = int(self.bir_year)
            if year < 1900:
                return False
            if year > int(current_year):
                return False
            # 出生月、当前月
            self.bir_mon = self.id_num[10:12]
            current_month = date.today().strftime("%m")
            if int(self.bir_mon) > 12 | int(self.bir_mon) < 1:
                return False
            # 出生日、当前日
            self.bir_day = self.id_num[12:14]
            current_day = date.today().strftime("%d")
            mon = int(self.bir_mon)
            day = int(self.bir_day)
            if day < 1:
                return False
            else:
                if mon == 2 & day > 28:
                    return False
                elif mon == 4 | mon == 6 | mon == 9 | mon == 11:
                    if day > 30:
                        return False
                else:
                    if day > 31:
                        return False
            # 年龄计算
            comp_year = int(current_year) - int(self.bir_year)
            comp_month = int(current_month) - int(self.bir_mon)
            comp_day = int(current_day) - int(self.bir_day)
            if comp_month > 0:
                self.age = comp_year
            elif comp_month == 0 & comp_day >= 0:
                self.age = comp_year
            else:
                self.age = comp_year - 1
            # 2位派出所代码
            self.order_code = self.id_num[14:16]
            # 性别
            self.gender_code = self.id_num[16:17]
            if int(self.gender_code) % 2 == 0:
                self.gender = '女'
            else:
                self.gender = '男'
            # 末位校验码
            self.checkcode = self.id_num[17:18]
            self.digits = []
            self.sum = 0
            for value in range(0, 17):
                self.digits.append(int(self.id_num[value]))
                self.sum += IDnumber.weights[value] * self.digits[value]

            if self.id_num[value + 1] is 'X':
                self.digits.append(self.id_num[value + 1])
            elif self.id_num[value + 1] is 'x':
                self.digits.append(self.id_num[value + 1])
            else:
                self.digits.append(int(self.id_num[value + 1]))

            # 判断余数与正确的校验码是否对应
            for key, value in IDnumber.mod_codes.items():
                if self.sum % 11 == key:
                    if key == 2:
                        if self.digits[17] is 'X':
                            return True
                        elif self.digits[17] is 'x':
                            return True
                        else:
                            return False
                    else:
                        if self.digits[17] is 'X':
                            return False
                        elif self.digits[17] is 'x':
                            return False
                        elif self.digits[17] != value:
                            return False
                        else:
                            return True
                else:
                    pass

    def show_info(self, judge=True):
        """显示身份证是否存在，及有关信息"""
        if judge == True:  # 输入参数为检验数据合理的标识
            print("\n———————————————————————————————————")
            print("身份证号码 " + self.id_num + " 有存在的可能性。")
            print("籍贯：" + self.native_place)
            print("性别：" + self.gender + "\t年龄：" + str(self.age))
            print("出生日期：" + self.bir_date + "\n")
        else:
            print("\n———————————————————————————————————")
            print("身份证号码 " + self.id_num + " 不存在！\n")

    def check(self, num):
        self.number_test(num)
        self.handle_id_num()
        res = self.judge_id_num()
        if res:
            return (self.native_place, self.age, self.bir_date)
        else:
            return None


if __name__ =="__main__":
    obj = IDnumber()
    res = obj.check("211421199304016015")
    # 41152419930414473X
    print(res)
    # obj.handle_id_num()
    # res = obj.judge_id_num()
    # obj.show_info(res)
