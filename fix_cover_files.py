#!/usr/bin/env python3
"""
Исправляет ссылки на файлы обложек в HTML, находя реальные имена
"""
import csv
import os
import re
import glob

def parse_date(dt_string):
    """Парсит дату из формата 'YYYY-MM-DD HH:MM:SS'"""
    return dt_string.split(' ')[0]

def escape_html(text):
    """Экранирует HTML спецсимволы"""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

def find_actual_cover_file(name, date):
    """Ищет фактический файл обложки"""
    year = date.split('-')[0] if date else "unknown"
    
    # Список всех файлов в covers_medium за этот год
    pattern = f"covers_medium/cover_{year}_*"
    files = glob.glob(pattern)
    
    # Создаем упрощенное имя для поиска
    search_name = name.replace('№', 'N').replace('–', '-').replace(' ', '_')
    search_name = re.sub(r'[()]', '', search_name)
    
    # Ищем подходящий файл
    for filepath in files:
        filename = os.path.basename(filepath)
        # Проверяем, содержит ли файл основу искомого имени
        if search_name.replace('-', '').replace('_', '').lower() in filename.replace('-', '').replace('_', '').lower():
            return filename
    
    # Если не нашли точно, ищем по номеру (есть в скобках)
    number_match = re.search(r'(\d+)', name)
    if number_match:
        number = number_match.group(1)
        for filepath in files:
            filename = os.path.basename(filepath)
            if f'_{number}_' in filename or filename.endswith(f'_{number}.jpg'):
                return filename
    
    print(f"⚠️ Не нашел файл для: {name} ({date})")
    return "fav.jpeg"

def generate_cover_html(name, date, pdf_link):
    """Генерирует HTML для одной обложки"""
    img_file = find_actual_cover_file(name, date)
    img_src = f"covers_medium/{img_file}"
    
    # Форматируем дату
    date_only = parse_date(date) if date else ""
    
    # Форматируем номер
    name_escaped = escape_html(name)
    
    # Простая ссылка без модального окна
    html = f'''<div class="cover-item">
    <a href="{pdf_link}" target="_blank">
        <div class="cover-image">
            <img src="{img_src}" alt="Обложка {name_escaped}" loading="lazy">
        </div>
    </a>
    <div class="cover-info">
        <div class="cover-number">{name_escaped}</div>
        <div class="cover-date">{date_only}</div>
    </div>
</div>'''
    
    return html

def main():
    # Читаем новый список
    issues = []
    with open('newlist.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['issue'] and row['issue_name']:
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
    
    # Читаем существующий index.html
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Генерируем новый HTML для всех обложек
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

