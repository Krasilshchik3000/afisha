#!/usr/bin/env python3
"""
Создает правильный index.html используя файлы из covers_medium
с правильным поиском всех форматов имен
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
    
    if not files:
        return None
    
    # Извлекаем номер из названия (например "№ 12 (58)")
    number_match = re.search(r'№\s*(\d+)', name)
    bracket_match = re.search(r'\((\d+)\)', name)
    
    if bracket_match:
        bracket_num = bracket_match.group(1)
        # Ищем файлы с этим номером в скобках (например, 58 в (58))
        matching_files = []
        for filepath in files:
            filename = os.path.basename(filepath)
            # Ищем разные форматы: (58), _58_, N_12_58 и т.д.
            if f'({bracket_num})' in filename or f'_{bracket_num}_' in filename or f'_N_{number_match.group(1) if number_match else ""}_{bracket_num}_' in filename:
                matching_files.append(filename)
        
        if matching_files:
            matching_files.sort()
            return matching_files[0]  # Возвращаем файл с наименьшим индексом
    
    # Если не нашли по скобкам, ищем по номеру
    if number_match:
        number = number_match.group(1)
        for filepath in files:
            filename = os.path.basename(filepath)
            if f'№ {number}' in filename or f'_N_{number}_' in filename:
                matching_files = sorted([os.path.basename(f) for f in files if f'№ {number}' in os.path.basename(f) or f'_N_{number}_' in os.path.basename(f)])
                if matching_files:
                    return matching_files[0]
    
    return None

def generate_cover_html(name, date, pdf_link):
    """Генерирует HTML для одной обложки с hover preview"""
    year = date.split('-')[0] if date else "unknown"
    
    # Ищем локальный файл обложки
    local_file = find_local_cover(name, year)
    
    if local_file:
        cover_src = f"covers_medium/{local_file}"
    else:
        print(f"⚠️ Не нашел файл для: {name} ({year})")
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
    }
    '''
    
    # Находим закрывающий тег </head> и вставляем стили
    if 'hover-preview' not in html_content:
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
    if 'hover-preview' not in html_content or 'positionPreview' not in html_content:
        html_content = html_content.replace('</body>', f'{hover_js}\n</body>')
    
    # Сохраняем
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ index.html обновлен с {len(issues)} обложками")
    print(f"🔍 Hover preview настроен")

if __name__ == "__main__":
    main()

