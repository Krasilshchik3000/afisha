#!/usr/bin/env python3
"""
Регенерирует index.html с правильными данными
"""
import csv
import os
import glob
import re
from urllib.parse import quote

def parse_date(dt_string):
    return dt_string.split(' ')[0] if dt_string else ""

def escape_html(text):
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

def find_local_cover(name, year):
    pattern = f"covers_medium/cover_{year}_*"
    files = glob.glob(pattern)
    
    if not files:
        return None
    
    # Сначала ищем точное совпадение по названию
    for filepath in files:
        filename = os.path.basename(filepath)
        # Убираем расширение и индексы для сравнения
        base_name = filename.replace('.jpg', '')
        # Проверяем, содержит ли имя файла название номера
        if name in base_name:
            return filename
    
    # Если не нашли точное совпадение, используем старую логику
    number_match = re.search(r'№\s*(\d+)', name)
    bracket_match = re.search(r'\((\d+)\)', name)
    
    if bracket_match:
        bracket_num = bracket_match.group(1)
        matching_files = []
        for filepath in files:
            filename = os.path.basename(filepath)
            if f'({bracket_num})' in filename or f'_{bracket_num}_' in filename:
                matching_files.append(filename)
        
        if matching_files:
            matching_files.sort()
            return matching_files[0]
    
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
    year = date.split('-')[0] if date else "unknown"
    
    local_file = find_local_cover(name, year)
    
    if local_file:
        cover_src = f"covers_medium/{local_file}"
    else:
        cover_src = "fav.jpeg"
    
    date_only = parse_date(date)
    name_escaped = escape_html(name)
    
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
    
    issues.sort(key=lambda x: x['date'])
    
    by_year = {}
    for issue in issues:
        year = issue['date'].split('-')[0] if '-' in issue['date'] else 'unknown'
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(issue)
    
    with open('index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
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
    
    new_html = '\n    '.join(new_content_parts)
    
    pattern = r'(<main>)([\s\S]*?)(</main>)'
    replacement = f'\\1\n    {new_html}\n\\3'
    html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
    
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
    
    if 'hover-preview' not in html_content:
        html_content = html_content.replace('</head>', f'<style>{hover_css}</style>\n</head>')
    
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
            
            const tempImg = new Image();
            tempImg.onload = function() {
                const maxWidth = window.innerWidth * 0.9;
                const maxHeight = window.innerHeight * 0.9;
                
                let displayWidth = tempImg.width;
                let displayHeight = tempImg.height;
                
                const scale = Math.min(maxWidth / tempImg.width, maxHeight / tempImg.height);
                if (scale < 1) {
                    displayWidth = tempImg.width * scale;
                    displayHeight = tempImg.height * scale;
                }
                
                preview.src = src;
                preview.style.width = displayWidth + 'px';
                preview.style.height = displayHeight + 'px';
                preview.style.display = 'block';
                
                positionPreview(event, displayWidth, displayHeight);
            };
            tempImg.src = src;
        }
        
        function positionPreview(event, displayWidth, displayHeight) {
            if (!preview) return;
            
            if (!displayWidth || !displayHeight) {
                displayWidth = preview.clientWidth || preview.width;
                displayHeight = preview.clientHeight || preview.height;
            }
            
            const windowWidth = window.innerWidth;
            const windowHeight = window.innerHeight;
            
            let left = event.clientX + 20;
            let top = event.clientY + 20;
            
            if (left + displayWidth > windowWidth) {
                left = event.clientX - displayWidth - 30;
                if (left < 10) left = 10;
            }
            
            if (top + displayHeight > windowHeight) {
                top = event.clientY - displayHeight - 30;
                if (top < 10) top = 10;
            }
            
            if (left < 10) left = 10;
            if (top < 10) top = 10;
            
            preview.style.left = left + 'px';
            preview.style.top = top + 'px';
        }
    </script>
    '''
    
    if 'hover-preview' not in html_content or 'positionPreview' not in html_content:
        html_content = html_content.replace('</body>', f'{hover_js}\n</body>')
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ index.html обновлен с {len(issues)} обложками")

if __name__ == "__main__":
    main()

