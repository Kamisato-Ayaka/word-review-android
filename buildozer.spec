[app]
title = 单词复习
package.name = wordreview
package.domain = org.wordreview

# 版本号
version = 1.0.0

# 源文件
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
source.include_dirs = assets

# 需求的Python包
# 固定Python 3.11（兼容性最好的稳定版）
# 简化依赖，避免C扩展编译失败
requirements = python3==3.11.9,kivy==2.3.0,lxml,python-docx,openai,httpx,Pillow,qrcode,pyjnius,certifi,charset-normalizer,idna,urllib3,requests,pydantic,typing-extensions,distro

# 架构：只构建 32 位 armeabi-v7a
android.arch = armeabi-v7a

# 自动接受SDK许可
android.accept_sdk_license = True

# API 级别
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 24

# 权限
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE

# 横屏/竖屏
orientation = portrait

# 全屏
fullscreen = 0

# 应用图标
# android.icon = assets/icon.png

# 启动画面
# android.presplash = assets/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1

# 输出目录
bin_dir = bin
