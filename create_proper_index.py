#!/usr/bin/env python3
"""
Создает правильный index.html используя ID для URL обложек
"""
import csv
import re
from pathlib import Path

def parse_date(dt_string):
    """Парсит дату из формата 'YYYY-MM-DD HH:MM:SS'"""
    return dt_string.split(' ')[0] if dt_string else ""

def escape_html(text):
    """Экранирует HTML спецсимволы"""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

def generate_cover_html(name, date, pdf_link, id_number):
    """Генерирует HTML для одной обложки"""
    # URL обложки из newlist.csv (используем ID)
    cover_url = f"https://archivarius-public.s3.us-west-2.amazonaws.com/rima/print/scraped_printed_issue/{id_number}/cover.jpg"
    
    # Форматируем дату
    date_only = parse_date(date)
    
    # Форматируем номер
    name_escaped = escape_html(name)
    
    # Простая ссылка без модального окна
    html = f'''<div class="cover-item">
    <a href="{pdf_link}" target="_blank">
        <div class="cover-image">
            <img src="{cover_url}" alt="Обложка {name_escaped}" loading="lazy" onerror="this.src='fav.jpeg'">
        </div>
    </a>
    <div class="cover-info">
        <div class="cover-number">{name_escaped}</div>
        <div class="cover-date">{date_only}</div>
    </div>
</div>'''
    
    return html

def read_template():
    """Читает шаблон index.html"""
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

def main():
    # Читаем новый список
    issues = []
    with open('newlist.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['issue'] and row['issue_name'] and row['id']:
                issues.append({
                    'name': row['issue_name'].strip(),
                    'date': row['issue_dt'].strip(),
                    'pdf': row['issue'].strip(),
                    'id': row['id'].strip()
                })
    
    print(f"Найдено {len(issues)} выпусков в newlist.csv")
    
    # Сортируем по дате
    issues.sort(key=lambda x: x['date'])
    
    # Группируем по годам
    by_year = {}
    for issue in issues:
        year = issue['date'].split('-')[0] if '-' in issue['date'] else 'unknown'
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(issue)
    
    # Читаем шаблон
    html_content = read_template()
    
    # Генерируем новый HTML для всех обложек
    new_content_parts = []
    
    for year in sorted(by_year.keys()):
        year_issues = by_year[year]
        new_content_parts.append(f'<section class="year-section"><h2 class="year-title">{year}</h2><div class="covers-grid">')
        
        for issue in year_issues:
            cover_html = generate_cover_html(
                issue['name'],
                issue['date'],
                issue['pdf'],
                issue['id']
            )
            new_content_parts.append(cover_html)
        
        new_content_parts.append('</div></section>')
    
    # Заменяем содержимое main
    new_html = '\n    '.join(new_content_parts)
    
    # Находим содержимое main и заменяем
    pattern = r'(<main>)([\s\S]*?)(</main>)'
    replacement = f'\\1\n    {new_html}\n\\3'
    html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
    
    # Сохраняем обновленный HTML
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ index.html обновлен с {len(issues)} обложками")
    print(f"📁 Сгруппировано по {len(by_year)} годам")

if __name__ == "__main__":
    main()

