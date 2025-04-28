#!/usr/bin/env python
"""
Google Generative AI (google.generativeai) モジュールのヘルプ情報を表示するスクリプト
"""

import google.genai as genai
import inspect

# モジュールヘルプを表示
print("\n=== GOOGLE GENERATIVE AI モジュールヘルプ ===")
print(help(genai))

# 属性と関数のリスト
print("\n=== モジュール内の関数と属性 ===")
for name, obj in inspect.getmembers(genai):
    if not name.startswith('_'):  # プライベート属性を除外
        print(f"{name}: {type(obj).__name__}")

# GenerativeModel クラスのヘルプ（存在する場合）
print("\n=== GenerativeModel クラスのヘルプ ===")
if hasattr(genai, 'GenerativeModel'):
    print(help(genai.GenerativeModel))
