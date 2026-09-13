# -*- coding: utf-8 -*-
"""复习计划逻辑模块 - 基于艾宾浩斯遗忘曲线"""
import calendar as cal
from datetime import datetime, timedelta
from collections import OrderedDict


class ReviewLogic:
    """复习计划管理器"""

    # 艾宾浩斯遗忘曲线复习间隔（天）
    REVIEW_DAYS = [1, 2, 4, 8, 15, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120,
                   132, 144, 156, 168, 180, 192, 204, 216, 228, 240, 252, 264,
                   276, 288, 300, 312, 324, 336, 348, 360, 365]

    def __init__(self, word_data):
        self.word_data = word_data
        now = datetime.now()
        self.current_year = now.year
        self.current_month = now.month

    def calculate_review_dates(self, add_date_str):
        """根据添加日期计算所有复习日期"""
        if not add_date_str:
            return {}
        try:
            add_date = datetime.strptime(add_date_str, "%Y-%m-%d")
            result = {}
            for day in self.REVIEW_DAYS:
                result[f"d{day}"] = (add_date + timedelta(days=day)).strftime("%Y-%m-%d")
            return result
        except Exception:
            return {}

    def get_review_words(self):
        """获取所有需要复习的单词，按日期分组
        返回: {date_str: [word_dict, ...]}
        """
        review_map = {}
        for word in self.word_data.word_list:
            date_str = word.get("date", "")
            if not date_str:
                continue
            try:
                add_date = datetime.strptime(date_str, "%Y-%m-%d")
                for day in self.REVIEW_DAYS:
                    review_date = (add_date + timedelta(days=day)).strftime("%Y-%m-%d")
                    if review_date not in review_map:
                        review_map[review_date] = []
                    review_map[review_date].append(word)
            except Exception:
                continue
        return review_map

    def get_words_for_day(self, date_str):
        """获取指定日期的单词（录入+复习）"""
        add_words = []
        review_words = []
        for word in self.word_data.word_list:
            d = word.get("date", "")
            if not d:
                continue
            if d == date_str:
                add_words.append(word)
                continue
            try:
                add_date = datetime.strptime(d, "%Y-%m-%d")
                review_dates = [(add_date + timedelta(days=day)).strftime("%Y-%m-%d")
                                for day in self.REVIEW_DAYS]
                if date_str in review_dates:
                    review_words.append(word)
            except Exception:
                continue
        return add_words, review_words

    def get_month_calendar(self, year=None, month=None):
        """获取指定月份的日历数据
        返回: list of list of (day or 0, date_str, word_count)
        """
        if year is None:
            year = self.current_year
        if month is None:
            month = self.current_month
        month_cal = cal.Calendar(firstweekday=0).monthdayscalendar(year, month)
        review_words = self.get_review_words()
        result = []
        for week in month_cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({"day": 0, "date": "", "count": 0})
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    count = len(review_words.get(date_str, []))
                    # 加上当日录入的单词
                    add_count = len([w for w in self.word_data.word_list
                                     if w.get("date", "") == date_str])
                    week_data.append({
                        "day": day, "date": date_str,
                        "count": count + add_count
                    })
            result.append(week_data)
        return result

    def prev_month(self):
        """上个月"""
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1

    def next_month(self):
        """下个月"""
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1

    def get_month_label(self):
        """获取月份标题"""
        return f"{self.current_year}年{self.current_month}月"

    @staticmethod
    def today_str():
        """获取今天的日期字符串"""
        return datetime.now().strftime("%Y-%m-%d")
