#!/usr/bin/env python3
"""
Финальное исправление index.html с правильными путями к covers_medium и hover preview
"""
import csv
import os
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

def escape_for_filename(text):
    """Экранирует имя для использования в имени файла"""
    # Используем URL-кодирование для спецсимволов
    return text.replace('№', '%E2%84%96').replace('–', '%E2%80%93')

def generate_cover_html(name, date, pdf_link, id_number):
    """Генерирует HTML для одной обложки"""
    # Используем URL с Amazon S3 для обложек
    cover_url = f"https://archivarius-public.s3.us-west-2.amazonaws.com/rima/print/scraped_printed_issue/{id_number}/cover.jpg"
    
    # Используем файлы из covers_medium для hover preview
    year = date.split('-')[0] if date else "unknown"
    safe_name = escape_for_filename(name)
    covers_medium_url = f"covers_medium/cover_{year}_{safe_name}"
    
    # Форматируем дату
    date_only = parse_date(date)
    
    # Форматируем номер
    name_escaped = escape_html(name)
    
    # HTML с hover preview
    html = f'''<div class="cover-item">
    <a href="{pdf_link}" target="_blank">
        <div class="cover-image">
            <img src="{cover_url}" alt="Обложка {name_escaped}" loading="lazy" class="cover-thumbnail" data-full="{cover_url}" onerror="this.src='covers_medium/cover_{year}_{safe_name}_0.jpg'; this.onerror=null;">
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
    
    # Добавляем CSS для hover preview
    hover_css = '''
    .cover-thumbnail {
        cursor: pointer;
    }
    
    .cover-item {
        position: relative;
    }
    
    .hover-preview {
        position: fixed;
        z-index: 9999;
        pointer-events: none;
        border: 4px solid rgba(255, 255, 255, 0.95);
        border-radius: 8px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.95);
        background: white;
        padding: 15px;
        display: none;
        max-width: 95vw;
        max-height: 95vh;
        object-fit: contain;
        transform-origin: top left;
    }
    '''
    
    # Находим закрывающий тег </head> и вставляем стили
    html_content = html_content.replace('</head>', f'<style>{hover_css}</style>\n</head>')
    
    # Добавляем JavaScript для hover preview
    hover_js = '''
    <script>
        let preview = null;
        let hoverTimeout = null;
        
        document.addEventListener('DOMContentLoaded', function() {
            const covers = document.querySelectorAll('.cover-thumbnail');
            
            covers.forEach(function(cover) {
                cover.addEventListener('mouseenter', function(e) {
                    clearTimeout(hoverTimeout);
                    
                    const img = e.target;
                    const fullSrc = img.getAttribute('data-full') || img.src;
                    
                    if (!preview) {
                        preview = document.createElement('img');
                        preview.className = 'hover-preview';
                        document.body.appendChild(preview);
                    }
                    
                    preview.src = fullSrc;
                    
                    hoverTimeout = setTimeout(() => {
                        showPreview(e, fullSrc);
                    }, 200);
                });
                
                cover.addEventListener('mousemove', function(e) {
                    if (preview && preview.style.display !== 'none') {
                        positionPreview(e);
                    }
                });
                
                cover.addEventListener('mouseleave', function() {
                    clearTimeout(hoverTimeout);
                    if (preview) {
                        preview.style.display = 'none';
                    }
                });
            });
        });
        
        function showPreview(event, src) {
            if (!preview) return;
            
            const img = new Image();
            img.onload = function() {
                preview.src = src;
                positionPreview(event);
                preview.style.display = 'block';
            };
            img.src = src;
        }
        
        function positionPreview(event) {
            if (!preview) return;
            
            const img = preview;
            const rect = img.getBoundingClientRect();
            const imgWidth = rect.width;
            const imgHeight = rect.height;
            const windowWidth = window.innerWidth;
            const windowHeight = window.innerHeight;
            
            let left = event.clientX + 20;
            let top = event.clientY + 20;
            
            // Не выходим за правый край
            if (left + imgWidth > windowWidth) {
                left = event.clientX - imgWidth - 30;
                if (left < 10) left = 10;
            }
            
            // Не выходим за нижний край
            if (top + imgHeight > windowHeight) {
                top = event.clientY - imgHeight - 30;
                if (top < 10) top = 10;
            }
            
            // Не выходим за верхний и левый края
            if (left < 10) left = 10;
            if (top < 10) top = 10;
            
            img.style.left = left + 'px';
            img.style.top = top + 'px';
        }
    </script>
    '''
    
    # Вставляем JavaScript перед закрывающим тегом </body>
    html_content = html_content.replace('</body>', f'{hover_js}\n</body>')
    
    # Сохраняем обновленный HTML
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ index.html обновлен с {len(issues)} обложками")
    print(f"📁 Сгруппировано по {len(by_year)} годам")
    print(f"🔍 Hover preview настроен")

if __name__ == "__main__":
    main()

