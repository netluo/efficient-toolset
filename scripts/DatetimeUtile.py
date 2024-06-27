# -*- coding: utf-8 -*-
# @Time    : 2022/7/1 12:36
# @Author  : chengxiang.luo
# @Email   : andrew.luo1992@gmail.com
# @File    : DatetimeUtile.py
# @Software: PyCharm

import calendar
from datetime import datetime

from dateutil.relativedelta import relativedelta


class DateTimeUtil():

    def get_cur_month(self):
        # 获取当前月
        return datetime.now().strftime("%Y-%m")

    def get_last_month(self, number=1):
        # 获取前几个月
        month_date = datetime.now().date() - relativedelta(months=number)
        return month_date.strftime("%Y-%m")

    def get_next_month(self, number=1):
        # 获取后几个月
        month_date = datetime.now().date() + relativedelta(months=number)
        return month_date.strftime("%Y-%m")

    def get_cur_month_start(self):
        # 获取当前月的第一天
        month_str = datetime.now().strftime('%Y-%m')
        return '{}-01'.format(month_str)

    def get_cur_month_end(self):
        # 获取当前月的最后一天
        '''
        param: month_str 月份，2021-04
        '''
        # return: 格式 %Y-%m-%d

        month_str = datetime.now().strftime('%Y-%m')
        year, month = int(month_str.split('-')[0]), int(month_str.split('-')[1])
        end = calendar.monthrange(year, month)[1]
        return '{}-{}-{}'.format(year, month, end)

    def get_last_month_start(self, month_str=None):
        # 获取上一个月的第一天
        '''
        param: month_str 月份，2021-04
        '''
        # return: 格式 %Y-%m-%d
        if not month_str:
            month_str = datetime.now().strftime('%Y-%m')
        year, month = int(month_str.split('-')[0]), int(month_str.split('-')[1])
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
        return '{}-{}-01'.format(year, month)

    def get_next_month_start(self, month_str=None):
        # 获取下一个月的第一天
        '''
        param: month_str 月份，2021-04
        '''
        # return: 格式 %Y-%m-%d
        if not month_str:
            month_str = datetime.now().strftime('%Y-%m')
        year, month = int(month_str.split('-')[0]), int(month_str.split('-')[1])
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        return '{}-{}-01'.format(year, month)

    def get_last_month_end(self, month_str=None):
        # 获取上一个月的最后一天
        '''
        param: month_str 月份，2021-04
        '''
        # return: 格式 %Y-%m-%d
        if not month_str:
            month_str = datetime.now().strftime('%Y-%m')
        year, month = int(month_str.split('-')[0]), int(month_str.split('-')[1])
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
        end = calendar.monthrange(year, month)[1]
        return '{}-{}-{}'.format(year, month, end)

    def get_next_month_end(self, month_str=None):
        # 获取下一个月的最后一天
        '''
        param: month_str 月份，2021-04
        '''
        # return: 格式 %Y-%m-%d
        if not month_str:
            month_str = datetime.now().strftime('%Y-%m')
        year, month = int(month_str.split('-')[0]), int(month_str.split('-')[1])
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        end = calendar.monthrange(year, month)[1]
        return '{}-{}-{}'.format(year, month, end)


if __name__ == '__main__':
    # 获取当前月
    print('当前月', DateTimeUtil().get_cur_month())
    # 获取上一个月
    print('上一个月', DateTimeUtil().get_last_month())
    # 获取上两个月
    print('上两个月', DateTimeUtil().get_last_month(number=2))
    # 获取下一个月
    print('下一个月', DateTimeUtil().get_next_month())
    # 获取下两个月
    print('下两个月', DateTimeUtil().get_next_month(number=2))
    # 获取当前月的第一天
    print('当前月的第一天', DateTimeUtil().get_cur_month_start())
    # 获取当前月的最后一天
    print('当前月的最后一天', DateTimeUtil().get_cur_month_end())
    # 获取上个月的第一天
    print('上个月的第一天', DateTimeUtil().get_last_month_start())
    # 获取下个月的第一天
    print('下个月的第一天', DateTimeUtil().get_next_month_start())
    # 获取上个月的最后一天
    print('上个月的最后一天', DateTimeUtil().get_last_month_end())
    # 获取下个月的最后一天
    print('下个月的最后一天', DateTimeUtil().get_next_month_end())
