#!/usr/bin/env bash
# 生成 labels.txt 從 data/train 資料夾
if [ ! -d "data/train" ]; then
  echo "請先準備 data/train"
  exit 1
fi
ls data/train | sort > labels.txt
echo "labels.txt 已生成"


