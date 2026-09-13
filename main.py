# -*- coding: utf-8 -*-
"""单词复习软件 - Android版 (Kivy)"""
import os
import sys
import threading
import random
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.filechooser import FileChooserListView
from kivy.utils import platform

# 业务逻辑模块
from word_data import WordData
from review_logic import ReviewLogic
from doc_generator import DocGenerator, FONT_SIZE_POINTS
from ai_chat import AIChat


# 获取存储目录（Android上使用应用私有目录）
def get_storage_dir():
    if platform == 'android':
        from android.storage import app_storage_path
        return app_storage_path()
    return os.path.dirname(os.path.abspath(__file__))


STORAGE_DIR = get_storage_dir()
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


class WordReviewApp(App):
    """主应用"""

    def build(self):
        self.title = "单词复习"
        # 初始化业务逻辑
        self.word_data = WordData(STORAGE_DIR)
        self.review_logic = ReviewLogic(self.word_data)
        self.doc_gen = DocGenerator()
        self.ai_chat = AIChat(os.path.join(STORAGE_DIR, "ai_config.txt"))

        # 选中状态
        self.selected_indices = set()

        # 创建屏幕管理器
        self.sm = ScreenManager()
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(VocabScreen(name='vocab'))
        self.sm.add_widget(ReviewScreen(name='review'))
        self.sm.add_widget(DocScreen(name='doc'))
        self.sm.add_widget(AIScreen(name='ai'))
        self.sm.add_widget(SettingsScreen(name='settings'))
        return self.sm


# ==================== 主屏幕 ====================
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))

        title = Label(text='单词复习软件', font_size='24sp', size_hint_y=0.2)
        layout.add_widget(title)

        buttons = [
            ('词汇管理', 'vocab'),
            ('复习计划', 'review'),
            ('生成文档', 'doc'),
            ('AI助手', 'ai'),
            ('设置', 'settings'),
        ]
        for text, screen in buttons:
            btn = Button(text=text, font_size='18sp', size_hint_y=0.15)
            btn.bind(on_press=lambda inst, s=screen: self.switch_to(s))
            layout.add_widget(btn)

        layout.add_widget(Label(size_hint_y=0.1))
        self.add_widget(layout)

    def switch_to(self, screen):
        self.manager.current = screen


# ==================== 词汇管理屏幕 ====================
class VocabScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_pre_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))

        # 顶部按钮栏
        top_bar = BoxLayout(size_hint_y=0.1, spacing=dp(5))
        back_btn = Button(text='返回', size_hint_x=0.15)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        top_bar.add_widget(back_btn)

        add_btn = Button(text='添加', size_hint_x=0.15)
        add_btn.bind(on_press=self.show_add_dialog)
        top_bar.add_widget(add_btn)

        select_all_btn = Button(text='全选', size_hint_x=0.15)
        select_all_btn.bind(on_press=self.select_all)
        top_bar.add_widget(select_all_btn)

        invert_btn = Button(text='反选', size_hint_x=0.15)
        invert_btn.bind(on_press=self.invert_selection)
        top_bar.add_widget(invert_btn)

        clear_btn = Button(text='清空', size_hint_x=0.15)
        clear_btn.bind(on_press=self.clear_selection)
        top_bar.add_widget(clear_btn)

        save_btn = Button(text='保存', size_hint_x=0.15)
        save_btn.bind(on_press=self.save_words)
        top_bar.add_widget(save_btn)

        layout.add_widget(top_bar)

        # 统计信息
        app = App.get_running_app()
        count_label = Label(
            text=f'共 {len(app.word_data.word_list)} 个单词，已选 {len(app.selected_indices)} 个',
            size_hint_y=0.05
        )
        layout.add_widget(count_label)
        self.count_label = count_label

        # 单词列表
        scroll = ScrollView()
        self.list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(2))
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        scroll.add_widget(self.list_layout)
        layout.add_widget(scroll)

        self.refresh_list()
        self.add_widget(layout)

    def refresh_list(self):
        app = App.get_running_app()
        self.list_layout.clear_widgets()
        for idx, word in enumerate(app.word_data.word_list):
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
            cb = CheckBox(size_hint_x=0.1)
            cb.active = idx in app.selected_indices
            cb.bind(active=lambda inst, val, i=idx: self.toggle_select(i, val))
            row.add_widget(cb)

            word_label = Label(text=word.get('word', ''), size_hint_x=0.3, font_size='14sp')
            row.add_widget(word_label)

            meaning_label = Label(text=word.get('meaning', ''), size_hint_x=0.4,
                                  font_size='12sp', text_size=(None, None))
            row.add_widget(meaning_label)

            date_label = Label(text=word.get('date', ''), size_hint_x=0.15, font_size='10sp')
            row.add_widget(date_label)

            edit_btn = Button(text='编辑', size_hint_x=0.15)
            edit_btn.bind(on_press=lambda inst, i=idx: self.show_edit_dialog(i))
            row.add_widget(edit_btn)

            del_btn = Button(text='删', size_hint_x=0.1)
            del_btn.bind(on_press=lambda inst, i=idx: self.delete_word(i))
            row.add_widget(del_btn)

            self.list_layout.add_widget(row)
        self.count_label.text = (
            f'共 {len(app.word_data.word_list)} 个单词，'
            f'已选 {len(app.selected_indices)} 个'
        )

    def toggle_select(self, idx, value):
        app = App.get_running_app()
        if value:
            app.selected_indices.add(idx)
        else:
            app.selected_indices.discard(idx)
        self.count_label.text = (
            f'共 {len(app.word_data.word_list)} 个单词，'
            f'已选 {len(app.selected_indices)} 个'
        )

    def select_all(self, instance):
        app = App.get_running_app()
        app.selected_indices = set(range(len(app.word_data.word_list)))
        self.refresh_list()

    def invert_selection(self, instance):
        app = App.get_running_app()
        all_idx = set(range(len(app.word_data.word_list)))
        app.selected_indices = all_idx - app.selected_indices
        self.refresh_list()

    def clear_selection(self, instance):
        app = App.get_running_app()
        app.selected_indices.clear()
        self.refresh_list()

    def save_words(self, instance):
        app = App.get_running_app()
        app.word_data.renumber()
        app.word_data.save_vocabulary()
        self.show_popup('提示', '词库已保存')

    def show_add_dialog(self, instance):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        word_input = TextInput(hint_text='单词', multiline=False)
        meaning_input = TextInput(hint_text='释义')
        date_input = TextInput(hint_text='日期 (YYYY-MM-DD, 留空为今天)', multiline=False)
        content.add_widget(word_input)
        content.add_widget(meaning_input)
        content.add_widget(date_input)

        btn_box = BoxLayout(size_hint_y=0.2, spacing=dp(10))
        cancel_btn = Button(text='取消')
        ok_btn = Button(text='确定')
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(ok_btn)
        content.add_widget(btn_box)

        popup = Popup(title='添加单词', content=content, size_hint=(0.9, 0.7))

        def do_add(*args):
            word = word_input.text.strip()
            meaning = meaning_input.text.strip()
            date_str = date_input.text.strip()
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            if word and meaning:
                app = App.get_running_app()
                app.word_data.add_word(word, meaning, date_str)
                self.refresh_list()
                popup.dismiss()

        ok_btn.bind(on_press=do_add)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_edit_dialog(self, idx):
        app = App.get_running_app()
        word = app.word_data.word_list[idx]
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        word_input = TextInput(text=word.get('word', ''), multiline=False)
        meaning_input = TextInput(text=word.get('meaning', ''))
        date_input = TextInput(text=word.get('date', ''), multiline=False)
        content.add_widget(word_input)
        content.add_widget(meaning_input)
        content.add_widget(date_input)

        btn_box = BoxLayout(size_hint_y=0.2, spacing=dp(10))
        cancel_btn = Button(text='取消')
        ok_btn = Button(text='确定')
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(ok_btn)
        content.add_widget(btn_box)

        popup = Popup(title='编辑单词', content=content, size_hint=(0.9, 0.7))

        def do_edit(*args):
            app.word_data.update_word(idx, word_input.text.strip(),
                                       meaning_input.text.strip(),
                                       date_input.text.strip())
            self.refresh_list()
            popup.dismiss()

        ok_btn.bind(on_press=do_edit)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def delete_word(self, idx):
        app = App.get_running_app()
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text=f'确定删除 "{app.word_data.word_list[idx].get("word", "")}" ?'))
        btn_box = BoxLayout(size_hint_y=0.3, spacing=dp(10))
        cancel_btn = Button(text='取消')
        ok_btn = Button(text='删除')
        btn_box.add_widget(cancel_btn)
        btn_box.add_widget(ok_btn)
        content.add_widget(btn_box)

        popup = Popup(title='确认删除', content=content, size_hint=(0.7, 0.4))

        def do_delete(*args):
            app.word_data.delete_word(idx)
            app.selected_indices.clear()
            self.refresh_list()
            popup.dismiss()

        ok_btn.bind(on_press=do_delete)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def show_popup(self, title, text):
        popup = Popup(title=title, content=Label(text=text), size_hint=(0.7, 0.3))
        popup.open()


# ==================== 复习计划屏幕 ====================
class ReviewScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_pre_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))

        # 顶部导航
        top_bar = BoxLayout(size_hint_y=0.1, spacing=dp(5))
        back_btn = Button(text='返回', size_hint_x=0.2)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        top_bar.add_widget(back_btn)

        prev_btn = Button(text='上月', size_hint_x=0.15)
        prev_btn.bind(on_press=self.prev_month)
        top_bar.add_widget(prev_btn)

        self.month_label = Label(text=app.review_logic.get_month_label(),
                                 size_hint_x=0.3, font_size='16sp')
        top_bar.add_widget(self.month_label)

        next_btn = Button(text='下月', size_hint_x=0.15)
        next_btn.bind(on_press=self.next_month)
        top_bar.add_widget(next_btn)

        today_btn = Button(text='今天', size_hint_x=0.2)
        today_btn.bind(on_press=self.go_today)
        top_bar.add_widget(today_btn)

        layout.add_widget(top_bar)

        # 日历
        scroll = ScrollView()
        self.cal_layout = GridLayout(cols=7, size_hint_y=None, spacing=dp(2))
        self.cal_layout.bind(minimum_height=self.cal_layout.setter('height'))
        scroll.add_widget(self.cal_layout)
        layout.add_widget(scroll)

        self.refresh_calendar()
        self.add_widget(layout)

    def refresh_calendar(self):
        app = App.get_running_app()
        self.cal_layout.clear_widgets()
        self.month_label.text = app.review_logic.get_month_label()

        # 周标题
        weeks = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for w in weeks:
            lbl = Label(text=w, font_size='12sp', size_hint_y=None, height=dp(30))
            self.cal_layout.add_widget(lbl)

        today = ReviewLogic.today_str()
        cal_data = app.review_logic.get_month_calendar()
        for week in cal_data:
            for day_info in week:
                if day_info["day"] == 0:
                    lbl = Label(text='', size_hint_y=None, height=dp(80))
                    self.cal_layout.add_widget(lbl)
                else:
                    is_today = day_info["date"] == today
                    bg_color = (0.3, 0.8, 0.3, 1) if is_today else (0.2, 0.2, 0.2, 1)
                    text = f"{day_info['day']}"
                    if day_info["count"] > 0:
                        text += f"\n({day_info['count']})"
                    btn = Button(text=text, size_hint_y=None, height=dp(80),
                                 background_color=bg_color, font_size='11sp')
                    btn.bind(on_press=lambda inst, d=day_info["date"]: self.show_day_words(d))
                    self.cal_layout.add_widget(btn)

    def prev_month(self, instance):
        app = App.get_running_app()
        app.review_logic.prev_month()
        self.refresh_calendar()

    def next_month(self, instance):
        app = App.get_running_app()
        app.review_logic.next_month()
        self.refresh_calendar()

    def go_today(self, instance):
        app = App.get_running_app()
        now = datetime.now()
        app.review_logic.current_year = now.year
        app.review_logic.current_month = now.month
        self.refresh_calendar()
        self.show_day_words(ReviewLogic.today_str())

    def show_day_words(self, date_str):
        app = App.get_running_app()
        add_words, review_words = app.review_logic.get_words_for_day(date_str)

        content = BoxLayout(orientation='vertical', spacing=dp(5), padding=dp(10))
        content.add_widget(Label(text=f'{date_str}', font_size='16sp', size_hint_y=0.1))

        info = f'当日录入: {len(add_words)} 个\n需要复习: {len(review_words)} 个'
        content.add_widget(Label(text=info, size_hint_y=0.1))

        # 单词列表
        scroll = ScrollView()
        list_layout = GridLayout(cols=1, size_hint_y=None, spacing=dp(2))
        list_layout.bind(minimum_height=list_layout.setter('height'))

        all_words = []
        for w in add_words:
            all_words.append(("录入", w))
        for w in review_words:
            all_words.append(("复习", w))

        for tag, w in all_words:
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
            row.add_widget(Label(text=tag, size_hint_x=0.15, font_size='10sp'))
            row.add_widget(Label(text=w.get('word', ''), size_hint_x=0.3, font_size='12sp'))
            row.add_widget(Label(text=w.get('meaning', ''), size_hint_x=0.55, font_size='11sp'))
            list_layout.add_widget(row)

        scroll.add_widget(list_layout)
        content.add_widget(scroll)

        # 按钮
        btn_box = BoxLayout(size_hint_y=0.15, spacing=dp(10))
        close_btn = Button(text='关闭')
        gen_btn = Button(text='生成默写文档')
        btn_box.add_widget(close_btn)
        btn_box.add_widget(gen_btn)
        content.add_widget(btn_box)

        popup = Popup(title=f'{date_str} 单词', content=content, size_hint=(0.95, 0.9))

        all_w = add_words + review_words
        gen_btn.bind(on_press=lambda x: self.generate_for_day(date_str, all_w, popup))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def generate_for_day(self, date_str, words, parent_popup):
        app = App.get_running_app()
        parent_popup.dismiss()
        # 切换到文档生成界面
        app._pending_doc_words = words
        app._pending_doc_date = date_str
        self.manager.current = 'doc'


# ==================== 文档生成屏幕 ====================
class DocScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_pre_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))

        top_bar = BoxLayout(size_hint_y=0.1, spacing=dp(5))
        back_btn = Button(text='返回', size_hint_x=0.2)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        top_bar.add_widget(back_btn)
        top_bar.add_widget(Label(text='文档生成', font_size='16sp', size_hint_x=0.6))
        layout.add_widget(top_bar)

        # 格式选项
        format_box = GridLayout(cols=2, size_hint_y=0.4, spacing=dp(5), padding=dp(5))

        format_box.add_widget(Label(text='行高:', size_hint_x=0.3))
        row_spinner = Spinner(text=app.doc_gen.row_height,
                              values=['1.0', '1.5', '2.0', '2.5', '3.0'],
                              size_hint_x=0.7)
        row_spinner.bind(text=lambda inst, val: setattr(app.doc_gen, 'row_height', val))
        format_box.add_widget(row_spinner)

        format_box.add_widget(Label(text='英文字体:', size_hint_x=0.3))
        en_spinner = Spinner(text=app.doc_gen.english_font,
                             values=['Arial', 'Times New Roman', 'Calibri', 'Verdana', 'Courier New'],
                             size_hint_x=0.7)
        en_spinner.bind(text=lambda inst, val: setattr(app.doc_gen, 'english_font', val))
        format_box.add_widget(en_spinner)

        format_box.add_widget(Label(text='中文字体:', size_hint_x=0.3))
        cn_spinner = Spinner(text=app.doc_gen.chinese_font,
                             values=['微软雅黑', '宋体', '黑体', '楷体', '仿宋'],
                             size_hint_x=0.7)
        cn_spinner.bind(text=lambda inst, val: setattr(app.doc_gen, 'chinese_font', val))
        format_box.add_widget(cn_spinner)

        format_box.add_widget(Label(text='字号:', size_hint_x=0.3))
        size_spinner = Spinner(text=app.doc_gen.font_size,
                               values=list(FONT_SIZE_POINTS.keys()),
                               size_hint_x=0.7)
        size_spinner.bind(text=lambda inst, val: setattr(app.doc_gen, 'font_size', val))
        format_box.add_widget(size_spinner)

        format_box.add_widget(Label(text='框线样式:', size_hint_x=0.3))
        border_spinner = Spinner(text=app.doc_gen.border_style,
                                 values=['实线', '虚线', '点线', '双线', '无框'],
                                 size_hint_x=0.7)
        border_spinner.bind(text=lambda inst, val: setattr(app.doc_gen, 'border_style', val))
        format_box.add_widget(border_spinner)

        format_box.add_widget(Label(text='框线粗细:', size_hint_x=0.3))
        thick_spinner = Spinner(text=app.doc_gen.border_thickness,
                                values=['0.5磅', '1.0磅', '1.5磅', '2.0磅', '2.5磅', '3.0磅'],
                                size_hint_x=0.7)
        thick_spinner.bind(text=lambda inst, val: setattr(app.doc_gen, 'border_thickness', val))
        format_box.add_widget(thick_spinner)

        layout.add_widget(format_box)

        # 信息显示
        self.info_label = Label(text='', size_hint_y=0.1)
        layout.add_widget(self.info_label)

        # 显示待生成的单词
        if hasattr(app, '_pending_doc_words') and app._pending_doc_words:
            words = app._pending_doc_words
            date_str = getattr(app, '_pending_doc_date', None)
            self.info_label.text = f'待生成: {len(words)} 个单词' + (f' ({date_str})' if date_str else '')
        else:
            # 使用选中的单词
            words = [app.word_data.word_list[i] for i in sorted(app.selected_indices)]
            if words:
                self.info_label.text = f'使用选中的 {len(words)} 个单词'
            else:
                self.info_label.text = '未选择单词，将使用全部单词'

        # 生成按钮
        btn_box = BoxLayout(size_hint_y=0.15, spacing=dp(10), padding=dp(5))
        ordered_btn = Button(text='生成顺序版')
        ordered_btn.bind(on_press=lambda x: self.generate(ordered=True))
        shuffle_btn = Button(text='生成乱序版')
        shuffle_btn.bind(on_press=lambda x: self.generate(ordered=False))
        btn_box.add_widget(ordered_btn)
        btn_box.add_widget(shuffle_btn)
        layout.add_widget(btn_box)

        layout.add_widget(Label(size_hint_y=0.2))
        self.add_widget(layout)

    def generate(self, ordered=True):
        app = App.get_running_app()
        if hasattr(app, '_pending_doc_words') and app._pending_doc_words:
            words = app._pending_doc_words
            date_str = getattr(app, '_pending_doc_date', None)
            app._pending_doc_words = None
            app._pending_doc_date = None
        else:
            words = [app.word_data.word_list[i] for i in sorted(app.selected_indices)]
            if not words:
                words = app.word_data.word_list
            date_str = None

        if not words:
            self.show_popup('警告', '没有可用的单词')
            return

        # 在Android上保存到外部存储
        if platform == 'android':
            from android.storage import primary_external_storage_path
            folder = os.path.join(primary_external_storage_path(), 'WordReview')
        else:
            folder = os.path.join(STORAGE_DIR, 'output')

        os.makedirs(folder, exist_ok=True)

        try:
            files = app.doc_gen.generate_word_files(words, folder, ordered=ordered, date_str=date_str)
            if files:
                msg = f'生成成功！\n保存位置: {folder}\n\n'
                msg += '\n'.join(os.path.basename(f) for f in files)
                self.show_popup('成功', msg)
            else:
                self.show_popup('失败', '文档生成失败')
        except Exception as e:
            self.show_popup('错误', f'生成失败: {str(e)}')

    def show_popup(self, title, text):
        popup = Popup(title=title, content=Label(text=text), size_hint=(0.9, 0.6))
        popup.open()


# ==================== AI聊天屏幕 ====================
class AIScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chat_history = []

    def on_pre_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))

        # 顶部
        top_bar = BoxLayout(size_hint_y=0.1, spacing=dp(5))
        back_btn = Button(text='返回', size_hint_x=0.15)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        top_bar.add_widget(back_btn)

        self.provider_spinner = Spinner(text=app.ai_chat.current_provider,
                                        values=['豆包', 'DeepSeek'],
                                        size_hint_x=0.25)
        self.provider_spinner.bind(text=self.on_provider_change)
        top_bar.add_widget(self.provider_spinner)

        self.status_label = Label(text='状态: 未知', size_hint_x=0.35, font_size='11sp')
        top_bar.add_widget(self.status_label)

        check_btn = Button(text='检测', size_hint_x=0.15)
        check_btn.bind(on_press=self.check_connection)
        top_bar.add_widget(check_btn)

        settings_btn = Button(text='设置', size_hint_x=0.1)
        settings_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'settings'))
        top_bar.add_widget(settings_btn)

        layout.add_widget(top_bar)

        # 聊天记录
        self.chat_scroll = ScrollView()
        self.chat_label = Label(text='', size_hint_y=None, font_size='13sp',
                                text_size=(Window.width - dp(40), None))
        self.chat_label.bind(texture_size=self.chat_label.setter('size'))
        self.chat_scroll.add_widget(self.chat_label)
        layout.add_widget(self.chat_scroll)

        # 输入区
        input_box = BoxLayout(size_hint_y=0.25, spacing=dp(5))
        self.msg_input = TextInput(hint_text='输入消息...', multiline=True)
        input_box.add_widget(self.msg_input)

        side_box = BoxLayout(orientation='vertical', size_hint_x=0.2, spacing=dp(5))
        send_btn = Button(text='发送')
        send_btn.bind(on_press=self.send_message)
        side_box.add_widget(send_btn)
        clear_btn = Button(text='清空')
        clear_btn.bind(on_press=self.clear_chat)
        side_box.add_widget(clear_btn)
        input_box.add_widget(side_box)

        layout.add_widget(input_box)
        self.add_widget(layout)

    def on_provider_change(self, instance, value):
        app = App.get_running_app()
        app.ai_chat.current_provider = value
        app.ai_chat.save_config()

    def append_chat(self, sender, message):
        self.chat_history.append((sender, message))
        text = ''
        for s, m in self.chat_history:
            text += f'\n【{s}】\n{m}\n'
        self.chat_label.text = text
        # 滚动到底部
        Clock.schedule_once(lambda dt: setattr(self.chat_scroll, 'scroll_y', 0), 0.1)

    def send_message(self, instance):
        msg = self.msg_input.text.strip()
        if not msg:
            return
        self.append_chat('用户', msg)
        self.msg_input.text = ''

        app = App.get_running_app()

        def worker():
            success, response, tag = app.ai_chat.send_message(msg, [])
            Clock.schedule_once(lambda dt: self.on_ai_response(success, response, tag))

        threading.Thread(target=worker, daemon=True).start()
        self.append_chat('系统', '正在等待AI回复...')

    def on_ai_response(self, success, response, tag):
        # 移除最后一条"正在等待"消息
        if self.chat_history and self.chat_history[-1][0] == '系统':
            self.chat_history.pop()
        if success:
            self.append_chat(f'AI ({tag})', response)
        else:
            self.append_chat('错误', response)

    def clear_chat(self, instance):
        self.chat_history = []
        self.chat_label.text = ''

    def check_connection(self, instance):
        app = App.get_running_app()
        self.status_label.text = '状态: 检测中...'

        def worker():
            ok, msg = app.ai_chat.check_connection()
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f'状态: {msg}'))

        threading.Thread(target=worker, daemon=True).start()


# ==================== 设置屏幕 ====================
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_pre_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        top_bar = BoxLayout(size_hint_y=0.1, spacing=dp(5))
        back_btn = Button(text='返回', size_hint_x=0.2)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        top_bar.add_widget(back_btn)
        top_bar.add_widget(Label(text='AI设置', font_size='16sp', size_hint_x=0.6))
        layout.add_widget(top_bar)

        scroll = ScrollView()
        form = GridLayout(cols=1, size_hint_y=None, spacing=dp(10), padding=dp(10))
        form.bind(minimum_height=form.setter('height'))

        # 豆包配置
        form.add_widget(Label(text='=== 豆包配置 ===', font_size='15sp', size_hint_y=None, height=dp(30)))
        self.doubao_key = TextInput(text=app.ai_chat.doubao_api_key, multiline=False,
                                    size_hint_y=None, height=dp(40))
        form.add_widget(Label(text='API Key:', size_hint_y=None, height=dp(20)))
        form.add_widget(self.doubao_key)

        self.doubao_ep = TextInput(text=app.ai_chat.doubao_endpoint, multiline=False,
                                   size_hint_y=None, height=dp(40))
        form.add_widget(Label(text='Endpoint:', size_hint_y=None, height=dp(20)))
        form.add_widget(self.doubao_ep)

        self.doubao_model = TextInput(text=app.ai_chat.doubao_model, multiline=False,
                                      size_hint_y=None, height=dp(40))
        form.add_widget(Label(text='Model:', size_hint_y=None, height=dp(20)))
        form.add_widget(self.doubao_model)

        # DeepSeek配置
        form.add_widget(Label(text='=== DeepSeek配置 ===', font_size='15sp', size_hint_y=None, height=dp(30)))
        self.ds_key = TextInput(text=app.ai_chat.deepseek_api_key, multiline=False,
                                size_hint_y=None, height=dp(40))
        form.add_widget(Label(text='API Key:', size_hint_y=None, height=dp(20)))
        form.add_widget(self.ds_key)

        self.ds_ep = TextInput(text=app.ai_chat.deepseek_endpoint, multiline=False,
                               size_hint_y=None, height=dp(40))
        form.add_widget(Label(text='Endpoint:', size_hint_y=None, height=dp(20)))
        form.add_widget(self.ds_ep)

        self.ds_model = TextInput(text=app.ai_chat.deepseek_model, multiline=False,
                                  size_hint_y=None, height=dp(40))
        form.add_widget(Label(text='Model:', size_hint_y=None, height=dp(20)))
        form.add_widget(self.ds_model)

        scroll.add_widget(form)
        layout.add_widget(scroll)

        # 保存按钮
        save_btn = Button(text='保存设置', size_hint_y=0.1)
        save_btn.bind(on_press=self.save_settings)
        layout.add_widget(save_btn)

        self.add_widget(layout)

    def save_settings(self, instance):
        app = App.get_running_app()
        app.ai_chat.doubao_api_key = self.doubao_key.text.strip()
        app.ai_chat.doubao_endpoint = self.doubao_ep.text.strip()
        app.ai_chat.doubao_model = self.doubao_model.text.strip()
        app.ai_chat.deepseek_api_key = self.ds_key.text.strip()
        app.ai_chat.deepseek_endpoint = self.ds_ep.text.strip()
        app.ai_chat.deepseek_model = self.ds_model.text.strip()
        app.ai_chat.save_config()
        popup = Popup(title='提示', content=Label(text='设置已保存'), size_hint=(0.6, 0.3))
        popup.open()


if __name__ == '__main__':
    WordReviewApp().run()
