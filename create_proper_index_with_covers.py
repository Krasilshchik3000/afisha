#!/usr/bin/env python3
"""
Создает правильный index.html с файлами из covers_medium и hover preview
"""
import csv
import os
import glob
import re
from urllib.parse import quote

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
    # Создаем паттерн для поиска
    safe_name = name.replace('№', '').replace('–', '-').replace(' ', '_')
    
    # Ищем файлы по году
    pattern = f"covers_medium/cover_{year}_*"
    files = glob.glob(pattern)
    
    # Проверяем точное совпадение по имени номера
    for filepath in files:
        filename = os.path.basename(filepath)
        if name in filename:
            return filename
    
    return None

def generate_cover_html(name, date, pdf_link):
    """Генерирует HTML для одной обложки"""
    year = date.split('-')[0] if date else "unknown"
    
    # Ищем локальный файл обложки
    local_file = find_local_cover(name, year)
    
    if local_file:
        cover_src = f"covers_medium/{local_file}"
    else:
        # Fallback на Amazon S3
        cover_src = f"https://archivarius-public.s3.us-west-2.amazonaws.com/rima/print/scraped_printed_issue/1234/cover.jpg"
    
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

