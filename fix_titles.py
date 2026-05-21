#!/usr/bin/env python3
"""
修復 Christian 文章標題的腳本
1. 檢查 frontmatter 中的 title 是否正確
2. 重命名文件以使用正確的標題而不是 slug
"""

import os
import re

BASE_DIR = "/Users/chunsingyu/softwares/christian-bot/christian log/"

def extract_frontmatter(filepath):
    """從 markdown 文件中提取 YAML frontmatter"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 檢查是否有 frontmatter (在 --- 之間)
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if match:
        frontmatter_str = match.group(1)
        # 手動解析 title 欄位
        title_match = re.search(r'title:\s*["\']?([^"\']+)["\']?', frontmatter_str)
        if title_match:
            return {'title': title_match.group(1).strip()}
    return {}

def is_slug_filename(filename):
    """檢查文件名是否只是 slug（純英文數字）"""
    # 移除 .md 後綴
    name = filename.replace('.md', '')
    # 檢查是否只包含小寫字母、數字和連字符
    return bool(re.match(r'^[0-9a-z-]+$', name))

def sanitize_filename(title):
    """將標題轉換為安全的文件名"""
    # 移除或替換不安全的字符
    # 保留中文、英文、數字、括號等
    title = title.replace(':', '：')
    title = title.replace('/', '-')
    title = title.replace('\\', '-')
    title = title.replace('?', '')
    title = title.replace('!', '')
    title = title.replace('*', '')
    title = title.replace('"', '')
    title = title.replace('<', '')
    title = title.replace('>', '')
    title = title.replace('|', '')
    return title.strip()

def main():
    # 統計變量
    total_files = 0
    slug_files = 0
    renamed_files = 0
    skipped_files = 0
    error_files = 0

    # 找到所有 markdown 文件
    for root, dirs, files in os.walk(BASE_DIR):
        for filename in files:
            if not filename.endswith('.md'):
                continue

            total_files += 1
            filepath = os.path.join(root, filename)

            # 檢查是否是 slug 文件名
            if not is_slug_filename(filename):
                continue

            slug_files += 1

            # 讀取 frontmatter
            frontmatter = extract_frontmatter(filepath)

            if not frontmatter or 'title' not in frontmatter:
                print(f"⚠️  無法讀取 frontmatter 或缺少 title: {filepath}")
                error_files += 1
                continue

            title = frontmatter['title']

            # 檢查 title 是否已經是中文（正確的）
            if not re.search(r'[一-鿿]', title):
                print(f"⚠️  title 可能不正確（沒有中文）: {filepath} - title: {title}")
                skipped_files += 1
                continue

            # 生成新文件名
            new_filename = sanitize_filename(title) + '.md'
            new_filepath = os.path.join(root, new_filename)

            # 檢查目標文件是否已存在
            if os.path.exists(new_filepath):
                # 比較兩個文件的內容是否相同
                with open(filepath, 'r', encoding='utf-8') as f1:
                    content1 = f1.read()
                with open(new_filepath, 'r', encoding='utf-8') as f2:
                    content2 = f2.read()

                if content1 == content2:
                    # 內容相同，刪除 slug 文件
                    print(f"🗑️  刪除重複文件（內容相同）: {filename}")
                    os.remove(filepath)
                    renamed_files += 1
                else:
                    print(f"⚠️  目標文件已存在但內容不同，跳過: {filepath}")
                    skipped_files += 1
                continue

            # 重命名文件
            try:
                os.rename(filepath, new_filepath)
                print(f"✅ 重命名: {filename} -> {new_filename}")
                renamed_files += 1
            except Exception as e:
                print(f"❌ 重命名失敗: {filepath} - {e}")
                error_files += 1

    # 打印統計
    print("\n" + "="*50)
    print("修復完成統計:")
    print("="*50)
    print(f"總文件數: {total_files}")
    print(f"slug 文件名數量: {slug_files}")
    print(f"成功重命名/刪除: {renamed_files}")
    print(f"跳過文件數: {skipped_files}")
    print(f"錯誤文件數: {error_files}")
    print("="*50)

if __name__ == "__main__":
    main()
