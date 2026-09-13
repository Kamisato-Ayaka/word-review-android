#!/bin/bash
# 单词复习Android版 - 32位APK打包脚本
# 适用于 Ubuntu/Debian 或 WSL2
# 使用方法: bash build.sh

set -e

echo "========================================="
echo "  单词复习 Android APK 打包脚本"
echo "  目标架构: armeabi-v7a (32位)"
echo "========================================="

# 1. 安装系统依赖
echo "[1/5] 安装系统依赖..."
sudo apt update
sudo apt install -y \
    build-essential \
    git \
    python3 \
    python3-dev \
    python3-pip \
    openjdk-17-jdk \
    unzip \
    zip \
    autoconf \
    libtool \
    pkg-config \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libssl-dev \
    automake \
    gettext

# 2. 安装Python依赖
echo "[2/5] 安装Python依赖..."
pip3 install --upgrade pip
pip3 install buildozer cython==0.29.36

# 3. 设置Java环境
echo "[3/5] 配置Java环境..."
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
echo "JAVA_HOME=$JAVA_HOME"

# 4. 清理旧的构建
echo "[4/5] 清理旧构建..."
buildozer android clean || true

# 5. 开始打包
echo "[5/5] 开始打包APK (32位 armeabi-v7a)..."
echo "这可能需要30-60分钟（首次构建）..."
buildozer android debug

echo ""
echo "========================================="
echo "  打包完成！"
echo "  APK文件位于: bin/ 目录"
echo "  文件名类似: wordreview-1.0.0-arm64-v8a-debug.apk"
echo "  注意：由于设置了 android.arch = armeabi-v7a"
echo "  生成的APK是32位版本"
echo "========================================="
