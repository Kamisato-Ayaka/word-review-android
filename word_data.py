# -*- coding: utf-8 -*-
"""词汇数据管理模块"""
import os
import json
from datetime import datetime


class WordData:
    """词汇数据管理器"""

    SEPARATOR = "☠"

    def __init__(self, storage_dir):
        self.storage_dir = storage_dir
        self.word_list = []
        self.vocabulary_file = os.path.join(storage_dir, "vocabulary.txt")
        # 如果存储目录没有词库，从assets复制默认词库
        if not os.path.exists(self.vocabulary_file):
            assets_vocab = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "assets", "vocabulary.txt"
            )
            if os.path.exists(assets_vocab):
                import shutil
                shutil.copy2(assets_vocab, self.vocabulary_file)
        self.load_vocabulary()

    def load_vocabulary(self):
        """从文件加载词汇"""
        self.word_list = []
        if os.path.exists(self.vocabulary_file):
            with open(self.vocabulary_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        if self.SEPARATOR in line:
                            parts = line.split(self.SEPARATOR, 3)
                        else:
                            parts = line.split(" ", 3)
                        if len(parts) >= 4:
                            self.word_list.append({
                                "id": parts[0], "word": parts[1],
                                "meaning": parts[2], "date": parts[3]
                            })
                        elif len(parts) >= 3:
                            self.word_list.append({
                                "id": parts[0], "word": parts[1],
                                "meaning": parts[2], "date": ""
                            })

    def save_vocabulary(self):
        """保存词汇到文件"""
        with open(self.vocabulary_file, "w", encoding="utf-8") as f:
            for idx, word in enumerate(self.word_list, 1):
                date_str = word.get("date", "")
                f.write(f"{idx}{self.SEPARATOR}{word['word']}{self.SEPARATOR}"
                        f"{word['meaning']}{self.SEPARATOR}{date_str}\n")

    def add_word(self, word_text, meaning, date_str=""):
        """添加单词"""
        new_id = str(len(self.word_list) + 1)
        self.word_list.append({
            "id": new_id,
            "word": word_text,
            "meaning": meaning,
            "date": date_str
        })
        self.save_vocabulary()

    def update_word(self, index, word_text, meaning, date_str):
        """更新单词"""
        if 0 <= index < len(self.word_list):
            self.word_list[index]["word"] = word_text
            self.word_list[index]["meaning"] = meaning
            self.word_list[index]["date"] = date_str
            self.save_vocabulary()

    def delete_word(self, index):
        """删除单词"""
        if 0 <= index < len(self.word_list):
            self.word_list.pop(index)
            self.save_vocabulary()

    def renumber(self):
        """重新编号"""
        for idx, word in enumerate(self.word_list, 1):
            word["id"] = str(idx)
        self.save_vocabulary()

    def get_words_by_date(self, date_str):
        """获取指定日期录入的单词"""
        return [w for w in self.word_list if w.get("date", "") == date_str]

    def get_all_words(self):
        """获取所有单词"""
        return self.word_list
