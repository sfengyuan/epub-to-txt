#!/usr/bin/env python3
"""
EPUB to TXT Converter Core Module
"""
import os
import re
import time
import argparse
import zipfile
import html
import chardet
from pathlib import Path
from xml.dom import minidom
from defusedxml.minidom import parseString as safe_parse_string
from bs4 import BeautifulSoup

# ------------------------- 核心转换逻辑（保持不变） -------------------------
def safe_decode(data_bytes):
    """Safely decode bytes by prioritizing EPUB standard encodings."""
    for encoding in ['utf-8', 'utf-16']:
        try:
            return data_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    detected_encoding = chardet.detect(data_bytes)['encoding'] or 'utf-8'
    return data_bytes.decode(detected_encoding, errors='replace')


def get_spine_order(epub_path):
    """Extract the spine order of content files from the EPUB."""
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        try:
            # 解析container.xml
            container_data_bytes = zip_ref.read('META-INF/container.xml')
            container_str = safe_decode(container_data_bytes)
            container_dom = safe_parse_string(container_str)
            rootfile_path = container_dom.getElementsByTagName('rootfile')[0].getAttribute('full-path')
        except Exception as e:
            print(f"Error parsing container.xml: {e}")
            return []

        # 解析OPF文件
        try:
            opf_data_bytes = zip_ref.read(rootfile_path)
            opf_str = safe_decode(opf_data_bytes)
            opf_dom = safe_parse_string(opf_str)

            # 获取OPF文件所在目录
            opf_dir = os.path.dirname(rootfile_path)
            if opf_dir and not opf_dir.endswith('/'):
                opf_dir += '/'

            # 解析manifest条目
            manifest_items = {}
            for item in opf_dom.getElementsByTagName('item'):
                item_id = item.getAttribute('id')
                item_href = item.getAttribute('href')
                # 处理相对路径
                if opf_dir and not item_href.startswith('/'):
                    item_href = opf_dir + item_href
                manifest_items[item_id] = item_href

            # 获取spine顺序
            spine_items = []
            for itemref in opf_dom.getElementsByTagName('itemref'):
                idref = itemref.getAttribute('idref')
                if idref in manifest_items:
                    spine_items.append(manifest_items[idref])

            return spine_items
        except Exception as e:
            print(f"Error parsing OPF file: {e}")
            return []


def normalize_path(path):
    """Normalize path to handle both forward and backward slashes."""
    return path.replace('\\', '/').lstrip('/')


def clean_text(text):
    """Clean the extracted text."""
    text = html.unescape(text)
    text = re.sub(r'\n{2,}', '\n\n', text)
    text = re.sub(r'^[ \t]+$', '', text, flags=re.MULTILINE)
    return text


def html_to_text(html_content):
    """Convert HTML content to plain text."""
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    return clean_text(text)


def convert_epub_to_txt(epub_path, output_dir=None, merge=False):
    """Convert EPUB file to TXT files."""
    start_time = time.time()

    # 创建输出目录
    if output_dir is None:
        epub_name = os.path.splitext(os.path.basename(epub_path))[0]
        output_dir = epub_name
    os.makedirs(output_dir, exist_ok=True)

    # 获取spine顺序
    print(f"Reading spine order from {epub_path}...")
    spine_items = get_spine_order(epub_path)
    if not spine_items:
        print("Error: Could not determine spine order. Exiting.")
        return

    # 处理每个HTML文件
    print(f"Processing {len(spine_items)} HTML files...")
    processed_files = []
    total_size = 0

    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        file_map = {normalize_path(name).lower(): name for name in zip_ref.namelist()}

        for item_path in spine_items:
            norm_path = normalize_path(item_path)
            actual_path = file_map.get(norm_path.lower())

            if not actual_path:
                print(f"Warning: File not found in EPUB: {item_path}")
                continue

            if not actual_path.lower().endswith(('.html', '.xhtml', '.htm')):
                continue

            try:
                html_data = zip_ref.read(actual_path)
                html_content = safe_decode(html_data)
                text_content = html_to_text(html_content)

                txt_filename = os.path.splitext(os.path.basename(actual_path))[0] + '.txt'
                txt_path = os.path.join(output_dir, txt_filename)

                with open(txt_path, 'w', encoding='utf-8') as txt_file:
                    txt_file.write(text_content)

                file_size = len(text_content.encode('utf-8'))
                total_size += file_size
                processed_files.append((txt_filename, file_size, text_content))
                print(f"Converted: {actual_path} -> {txt_path} ({file_size} bytes)")

            except Exception as e:
                print(f"Error processing {actual_path}: {e}")

    # 合并文件（如果启用）
    if merge and processed_files:
        merged_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(epub_path))[0]}_merged.txt")
        with open(merged_path, 'w', encoding='utf-8') as merged_file:
            for index, (filename, _, content) in enumerate(processed_files):
                if index > 0:
                    merged_file.write("\n\n")
                merged_file.write(f"---{os.path.splitext(filename)[0]}---\n\n")
                merged_file.write(content)
        print(f"Created merged file: {merged_path}")

    # 输出统计信息
    elapsed_time = time.time() - start_time
    print("\nConversion statistics:")
    print(f"Files processed: {len(processed_files)}")
    print(f"Total size: {total_size} bytes")
    if processed_files:
        print(f"Average file size: {total_size // len(processed_files)} bytes")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")

# ------------------------- 命令行接口 -------------------------
def main_cli():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description='Convert EPUB files to TXT format.')
    parser.add_argument('epub_file', help='Path to the EPUB file')
    parser.add_argument('-m', '--merge', action='store_true', help='Merge all TXT files into a single file')
    parser.add_argument('-o', '--output', help='Output directory')
    args = parser.parse_args()

    if not os.path.isfile(args.epub_file):
        print(f"Error: EPUB file not found: {args.epub_file}")
        return

    convert_epub_to_txt(args.epub_file, args.output, args.merge)

# 保护命令行入口
if __name__ == "__main__":
    main_cli()
# epub_to_txt.py（保持不变，仅在最后添加以下两行）
# ------------------------- EXPORT MARKER -------------------------
__all__ = ['convert_epub_to_txt', 'main_cli']
