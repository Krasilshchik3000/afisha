#!/usr/bin/env python3
"""
Исправляет источники обложек и добавляет hover preview
"""
import csv
import os
import re
import glob

def parse_date(dt_string):
    """Парсит дату из формата 'YYYY-MM-DD HH:MM:SS'"""
    return dt_string.split(' ')[0] if dt_string else ""

def escape_html(text):
    """Экранирует HTML спецсимволы"""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

def find_actual_cover_file(name, date):
    """Ищет фактический файл обложки в covers_medium"""
    year = date.split('-')[0] if date else "unknown"
    
    # Список всех файлов в covers_medium за этот год
    pattern = f"covers_medium/cover_{year}_*"
    files = glob.glob(pattern)
    
    # Извлекаем номер из названия (например, "№ 1 (1)")
    # Ищем файлы, которые могут содержать этот номер
    for filepath in files:
        filename = os.path.basename(filepath)
        
        # Создаем паттерны для поиска
        # Номер может быть в разных форматах: № 1 (1), № 10–11 (10–11) и т.д.
        number_match = re.search(r'№\s*(\d+)', name)
        if number_match:
            number = number_match.group(1)
            # Ищем файлы с этим номером
            if f'№ {number}' in filename or f'_{number}_' in filename or f'_{number}.jpg' in filename:
                # Находим файл с наименьшим индексом
                files_with_number = [f for f in files if f'№ {number}' in os.path.basename(f)]
                if files_with_number:
                    files_with_number.sort()
                    return os.path.basename(files_with_number[0])
        
        # Альтернативный поиск по номеру в скобках
        bracket_match = re.search(r'\((\d+)\)', name)
        if bracket_match:
            bracket_num = bracket_match.group(1)
            if f'({bracket_num})' in filename:
                files_with_bracket = [f for f in files if f'({bracket_num})' in os.path.basename(f)]
                if files_with_bracket:
                    files_with_bracket.sort()
                    return os.path.basename(files_with_bracket[0])
    
    # Если не нашли, ищем по году и номеру без скобок
    clean_name = name.replace('№', '').replace('(', '').replace(')', '').replace(' ', '_').replace('–', '-')
    
    return None

def generate_cover_html(name, date, pdf_link):
    """Генерирует HTML для одной обложки с hover preview"""
    img_file = find_actual_cover_file(name, date)
    
    if not img_file:
        print(f"⚠️ Не найден файл для: {name} ({date})")
        # Используем URL из Amazon S3 как fallback
        img_src = f"https://archivarius-public.s3.us-west-2.amazonaws.com/rima/print/scraped_printed_issue/{name}/cover.jpg"
    else:
        img_src = f"covers_medium/{img_file}"
    
    # URL для полноразмерного изображения (из covers_medium)
    full_src = f"covers_medium/{img_file}" if img_file else "fav.jpeg"
    
    # Форматируем дату
    date_only = parse_date(date)
    
    # Форматируем номер
    name_escaped = escape_html(name)
    
    # Создаем уникальный ID для hover preview
    preview_id = f"preview_{hash(name + date)}"
    
    # HTML с hover preview
    html = f'''<div class="cover-item">
    <a href="{pdf_link}" target="_blank">
        <div class="cover-image">
            <img src="{img_src}" alt="Обложка {name_escaped}" loading="lazy" class="cover-thumbnail" data-full="{full_src}">
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
    
    # Читаем index.html
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
    
    # Добавляем CSS для hover preview
    hover_css = '''
    .cover-thumbnail {
        cursor: pointer;
        transition: opacity 0.2s;
    }
    
    .cover-item:hover .cover-image {
        position: relative;
        z-index: 1000;
    }
    
    .cover-item:hover .hover-preview {
        position: fixed;
        z-index: 9999;
        pointer-events: none;
        border: 3px solid rgba(255, 255, 255, 0.9);
        border-radius: 8px;
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.9);
        background: white;
        padding: 10px;
        display: block;
        max-width: 90vw;
        max-height: 90vh;
        object-fit: contain;
    }
    
    .hover-preview {
        display: none;
    }
    '''
    
    # Находим закрывающий тег </head> и вставляем стили
    html_content = html_content.replace('</head>', f'<style>{hover_css}</style>\n</head>')
    
    # Добавляем JavaScript для hover preview
    hover_js = '''
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const covers = document.querySelectorAll('.cover-thumbnail');
            
            covers.forEach(function(cover) {
                let preview = null;
                
                cover.addEventListener('mouseenter', function(e) {
                    const img = e.target;
                    const fullSrc = img.getAttribute('data-full');
                    
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.src = fullSrc;
                        preview.className = 'hover-preview';
                        document.body.appendChild(preview);
                    }
                    
                    // Позиционируем превью рядом с курсором
                    setTimeout(() => {
                        const updatePosition = (event) => {
                            const imgRect = img.getBoundingClientRect();
                            const mouseX = event.clientX;
                            const mouseY = event.clientY;
                            
                            // Получаем размеры изображения
                            const imgObj = new Image();
                            imgObj.src = fullSrc;
                            imgObj.onload = function() {
                                const maxWidth = Math.min(window.innerWidth * 0.9, imgObj.width);
                                const maxHeight = Math.min(window.innerHeight * 0.9, imgObj.height);
                                
                                // Сохраняем пропорции
                                const scale = Math.min(maxWidth / imgObj.width, maxHeight / imgObj.height);
                                preview.style.width = (imgObj.width * scale) + 'px';
                                preview.style.height = (imgObj.height * scale) + 'px';
                                
                                // Позиционируем с учетом размеров превью
                                const previewWidth = imgObj.width * scale + 20; // + отступы
                                const previewHeight = imgObj.height * scale + 20;
                                
                                let left = mouseX + 20;
                                let top = mouseY + 20;
                                
                                // Проверяем, не выходит ли за правый край
                                if (left + previewWidth > window.innerWidth) {
                                    left = mouseX - previewWidth - 20;
                                }
                                
                                // Проверяем, не выходит ли за нижний край
                                if (top + previewHeight > window.innerHeight) {
                                    top = mouseY - previewHeight - 20;
                                }
                                
                                preview.style.left = Math.max(10, left) + 'px';
                                preview.style.top = Math.max(10, top) + 'px';
                                preview.style.display = 'block';
                            };
                            
                            img.addEventListener('mousemove', updatePosition);
                            updatePosition({ clientX: mouseX, clientY: mouseY });
                        };
                        
                        cover.addEventListener('mousemove', updatePosition);
                    }, 100);
                });
                
                cover.addEventListener('mouseleave', function() {
                    if (preview) {
                        preview.style.display = 'none';
                    }
                });
            });
        });
    </script>
    '''
    
    # Вставляем JavaScript перед закрывающим тегом </body>
    html_content = html_content.replace('</body>', f'{hover_js}\n</body>')
    
    # Сохраняем обновленный HTML
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ index.html обновлен с {len(issues)} обложками")
    print(f"📁 Сгруппировано по {len(by_year)} годам")

if __name__ == "__main__":
    main()

