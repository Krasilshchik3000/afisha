#!/usr/bin/env python3
"""
Создает правильный index.html используя файлы из covers_medium
"""
import csv
import os
import glob
import re

def parse_date(dt_string):
    """Парсит дату из формата 'YYYY-MM-DD HH:MM:SS'"""
    return dt_string.split(' ')[0] if dt_string else ""

def escape_html(text):
    """Экранирует HTML спецсимволы"""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

def find_local_cover(name, year):
    """Ищет локальный файл обложки в covers_medium"""
    # Создаем список всех файлов за год
    pattern = f"covers_medium/cover_{year}_*"
    files = glob.glob(pattern)
    
    # Извлекаем номер из названия (например "№ 1 (1)")
    # Ищем файл с похожим номером
    number_match = re.search(r'№\s*(\d+)', name)
    
    if number_match:
        number = number_match.group(1)
        # Ищем файлы с этим номером
        for filepath in files:
            filename = os.path.basename(filepath)
            if f'№ {number}' in filename:
                # Находим файл с наименьшим индексом
                matching_files = sorted([f for f in files if f'№ {number}' in os.path.basename(f)])
                if matching_files:
                    return os.path.basename(matching_files[0])
    
    # Ищем по номеру в скобках
    bracket_match = re.search(r'\((\d+)\)', name)
    if bracket_match:
        bracket_num = bracket_match.group(1)
        for filepath in files:
            filename = os.path.basename(filepath)
            if f'({bracket_num})' in filename:
                matching_files = sorted([f for f in files if f'({bracket_num})' in os.path.basename(f)])
                if matching_files:
                    return os.path.basename(matching_files[0])
    
    return None

def generate_cover_html(name, date, pdf_link):
    """Генерирует HTML для одной обложки с hover preview"""
    year = date.split('-')[0] if date else "unknown"
    
    # Ищем локальный файл обложки
    local_file = find_local_cover(name, year)
    
    if local_file:
        cover_src = f"covers_medium/{local_file}"
        print(f"✅ Нашел файл: {name} -> {local_file}")
    else:
        print(f"⚠️ Не нашел файл для: {name}")
        cover_src = "fav.jpeg"  # fallback
    
    # Форматируем дату
    date_only = parse_date(date)
    
    # Форматируем номер
    name_escaped = escape_html(name)
    
    # HTML с hover preview
    html = f'''<div class="cover-item">
    <a href="{pdf_link}" target="_blank">
        <div class="cover-image">
            <img src="{cover_src}" alt="Обложка {name_escaped}" loading="lazy" class="cover-thumbnail" data-full="{cover_src}">
        </div>
    </a>
    <div class="cover-info">
        <div class="cover-number">{name_escaped}</div>
        <div class="cover-date">{date_only}</div>
    </div>
</div>'''
    
    return html

def main():
    # Читаем newlist.csv
    issues = []
    with open('newlist.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['issue'] and row['issue_name']:
                issues.append({
                    'name': row['issue_name'].strip(),
                    'date': row['issue_dt'].strip(),
                    'pdf': row['issue'].strip()
                })
    
    print(f"Найдено {len(issues)} выпусков")
    
    # Сортируем по дате
    issues.sort(key=lambda x: x['date'])
    
    # Группируем по годам
    by_year = {}
    for issue in issues:
        year = issue['date'].split('-')[0] if '-' in issue['date'] else 'unknown'
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(issue)
    
    # Читаем index.html
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Генерируем новый HTML
    new_content_parts = []
    
    for year in sorted(by_year.keys()):
        year_issues = by_year[year]
        new_content_parts.append(f'<section class="year-section"><h2 class="year-title">{year}</h2><div class="covers-grid">')
        
        for issue in year_issues:
            cover_html = generate_cover_html(
                issue['name'],
                issue['date'],
                issue['pdf']
            )
            new_content_parts.append(cover_html)
        
        new_content_parts.append('</div></section>')
    
    # Заменяем содержимое main
    new_html = '\n    '.join(new_content_parts)
    
    pattern = r'(<main>)([\s\S]*?)(</main>)'
    replacement = f'\\1\n    {new_html}\n\\3'
    html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
    
    # Сохраняем
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ index.html обновлен с {len(issues)} обложками")

if __name__ == "__main__":
    main()

