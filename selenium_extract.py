#!/usr/bin/env python3
import time
import json
import os
import requests
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from collections import defaultdict

def extract_with_selenium():
    """Извлечение данных с помощью Selenium"""

    # Настройки для headless браузера
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT1R7dx12qHVZLlhM6Jm9sKo28_qVuMR1CLtU99woNx7LaqBp0UREiuQHSAZ-1oFgKzQXNQeKKy1Emy/pubhtml"

        print("Загрузка страницы...")
        driver.get(url)

        # Ждем загрузки контента
        time.sleep(5)

        # Получаем HTML после выполнения JavaScript
        html = driver.page_source

        # Сохраняем для анализа
        with open('selenium_output.html', 'w', encoding='utf-8') as f:
            f.write(html)

        print("HTML сохранен в selenium_output.html")

        # Парсим с BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Ищем iframe
        iframes = soup.find_all('iframe')
        print(f"Найдено iframe: {len(iframes)}")

        if iframes:
            print("Переходим в iframe...")
            # Переходим в первый iframe по индексу
            driver.switch_to.frame(0)

            # Ждем загрузки контента в iframe
            time.sleep(3)

            # Получаем HTML из iframe
            iframe_html = driver.page_source

            # Сохраняем для анализа
            with open('iframe_output.html', 'w', encoding='utf-8') as f:
                f.write(iframe_html)

            print("HTML из iframe сохранен в iframe_output.html")

            # Парсим HTML из iframe
            iframe_soup = BeautifulSoup(iframe_html, 'html.parser')

            # Ищем таблицы в iframe
            tables = iframe_soup.find_all('table')
            print(f"Найдено таблиц в iframe: {len(tables)}")

            if tables:
                table = tables[0]
                rows = table.find_all('tr')
            else:
                print("Таблицы не найдены в iframe")
                driver.switch_to.default_content()
                return []
        else:
            # Если iframe нет, ищем таблицы в основном документе
            tables = soup.find_all('table')
            print(f"Найдено таблиц в основном документе: {len(tables)}")

            if not tables:
                print("Таблицы не найдены ни в iframe, ни в основном документе")
                return []

            table = tables[0]
            rows = table.find_all('tr')

        data = []
        for i, row in enumerate(rows):
            cols = row.find_all('td')
            if len(cols) >= 3:
                # Извлекаем данные в правильном порядке
                raw_date = cols[0].get_text(strip=True)  # Дата в формате гггг-мм-дд
                raw_number = cols[1].get_text(strip=True)  # Номер журнала
                image_url = ""

                # Ищем изображение
                img_tag = cols[2].find('img')
                if img_tag and 'src' in img_tag.attrs:
                    image_url = img_tag['src']

                if raw_date and raw_number and image_url:
                    # Фильтруем заголовки таблицы и неполные записи
                    if (raw_date in ['Дата', 'Выпуск'] or
                        raw_number in ['Выпуск', '№'] or
                        image_url == "" or
                        'lh3.googleusercontent.com' not in image_url):
                        continue

                    # Парсим дату
                    try:
                        # Дата уже в формате гггг-мм-дд
                        date_obj = raw_date  # Сохраняем как строку для сортировки
                        year = raw_date[:4]  # Извлекаем год из начала строки

                        data.append({
                            'number': raw_number,
                            'date': raw_date,
                            'year': year,
                            'image_url': image_url,
                            'date_obj': raw_date  # Для правильной сортировки
                        })

                        if i < 5:  # Показываем первые 5 записей
                            print(f"  {raw_number} - {raw_date} - {year} - {image_url[:50]}...")
                    except Exception as e:
                        print(f"Ошибка обработки строки {i}: {e}")
                        continue

        # Группируем по годам
        data_by_year = defaultdict(list)
        for item in data:
            data_by_year[item['year']].append(item)

        # Сортируем по годам, а внутри годов по дате
        sorted_data = {}
        for year in sorted(data_by_year.keys()):
            # Сортируем по дате внутри каждого года
            sorted_data[year] = sorted(data_by_year[year], key=lambda x: x['date_obj'])

        # Дополнительно сортируем все данные по дате для общей хронологии
        all_data_sorted = sorted(data, key=lambda x: x['date_obj'])

        # Возвращаемся в основной контент
        driver.switch_to.default_content()
        return sorted_data

    finally:
        driver.quit()

def generate_html_from_data(data, links, filename="index.html"):
    """Генерация упрощенного HTML с встроенными ссылками на PDF и локальными изображениями."""

    # Формируем HTML-код для всех обложек
    covers_html = ""
    for year in sorted(data.keys()):
        if year == "Неизвестный год":
            continue

        covers_html += f'<section class="year-section"><h2 class="year-title">{year}</h2><div class="covers-grid">'

        # Сортируем выпуски по дате, чтобы сохранить порядок
        sorted_items = sorted(data[year], key=lambda x: x['date_obj'])

        for i, item in enumerate(sorted_items):
            sanitized_number = item['number'].replace('/', '-')
            image_path = f"covers_medium/cover_{year}_{sanitized_number}_{i}.jpg"
            pdf_url = links.get(item['number'], '')

            covers_html += f'''
<div class="cover-item">
    <a href="{pdf_url}" target="_blank" onclick="return openPdfModal('{pdf_url}')">
        <div class="cover-image">
            <img src="{image_path}" alt="Обложка {item['number']}" loading="lazy">
        </div>
    </a>
    <div class="cover-info">
        <div class="cover-number">{item['number']}</div>
        <div class="cover-date">{item['date']}</div>
    </div>
</div>'''
        covers_html += '</div></section>'

    # Простой шаблон HTML с минимальным PDF-просмотрщиком
    html_template = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Архив обложек журнала Афиша</title>
    <link rel="stylesheet" href="styles_alt.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Grato+Grotesk:wght@400;600&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <style>
        body {{ font-family: 'Grato Grotesk', -apple-system, BlinkMacSystemFont, sans-serif; }}
        .pdf-modal {{ display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); }}
        .pdf-modal-content {{ background: #000; margin: auto; padding: 0; width: 90%; height: 90%; position: relative; }}
        .pdf-close {{ position: absolute; top: 10px; right: 20px; color: #fff; font-size: 30px; cursor: pointer; z-index: 1001; }}
        .pdf-container {{ width: 100%; height: 100%; overflow: auto; }}
        .pdf-loading {{ display: flex; align-items: center; justify-content: center; height: 100%; color: #ccc; }}
        .pdf-canvas {{ display: block; margin: 0 auto; max-width: 100%; height: auto; }}
    </style>
</head>
<body>
<header>
    <img src="fav.jpeg" alt="Логотип Афиши" class="logo">
    <div class="header-text">
        <strong>357 обложек «Афиши»</strong> Если нажать, откроется pdf всего номера
    </div>
</header>
<main>
    {covers_html}
</main>
<div class="pdf-modal" id="pdfModal">
    <div class="pdf-modal-content">
        <div class="pdf-close" onclick="closePdfModal()">×</div>
        <div class="pdf-container" id="pdfContainer">
            <div class="pdf-loading" id="pdfLoading">Загрузка PDF...</div>
        </div>
    </div>
</div>
<script>
let pdfDoc = null, currentPage = 1, scale = 1.0;

pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

function openPdfModal(pdfUrl) {{
    if (!pdfUrl || pdfUrl === '#') return false;

    document.getElementById('pdfModal').style.display = 'block';
    document.body.style.overflow = 'hidden';

    loadPDF(pdfUrl);
    return false; // Предотвращаем открытие ссылки в новой вкладке
}}

async function loadPDF(url) {{
    try {{
        document.getElementById('pdfLoading').style.display = 'flex';
        const loadingTask = pdfjsLib.getDocument(url);
        pdfDoc = await loadingTask.promise;
        currentPage = 1;
        scale = 1.0;
        renderPage(currentPage);
    }} catch (error) {{
        console.error('Ошибка загрузки PDF:', error);
        document.getElementById('pdfLoading').innerHTML = 'Ошибка загрузки PDF файла';
    }}
}}

async function renderPage(pageNum) {{
    try {{
        const page = await pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({{ scale }});
        const container = document.getElementById('pdfContainer');
        container.innerHTML = '';

        const canvas = document.createElement('canvas');
        canvas.className = 'pdf-canvas';
        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        await page.render({{ canvasContext: context, viewport }}).promise;
        container.appendChild(canvas);

    }} catch (error) {{
        console.error('Ошибка рендеринга страницы:', error);
    }} finally {{
        document.getElementById('pdfLoading').style.display = 'none';
    }}
}}

function closePdfModal() {{
    document.getElementById('pdfModal').style.display = 'none';
    document.getElementById('pdfContainer').innerHTML = '';
    pdfDoc = null;
    document.body.style.overflow = 'auto';
}}

window.onclick = (event) => {{
    if (event.target === document.getElementById('pdfModal')) {{
        closePdfModal();
    }}
}};

document.addEventListener('keydown', (event) => {{
    if (event.key === 'Escape') closePdfModal();
}});
</script>
<footer>
    <p>Данные взяты из Google Sheets таблицы</p>
</footer>
</body>
</html>"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"Упрощенный HTML '{filename}' создан.")

def download_image(url, filename):
    """Скачивает изображение по URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        with open(filename, 'wb') as f:
            f.write(response.content)

        print(f"Скачано: {filename}")
        return True

    except Exception as e:
        print(f"Ошибка скачивания {url}: {e}")
        return False

def download_all_images(data):
    """Скачивает все изображения из извлеченных данных"""
    images_dir = 'covers'
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    downloaded_count = 0
    total_images = sum(len(items) for items in data.values())
    
    print(f"\nНачинаю скачивание {total_images} обложек...")

    for year, items in data.items():
        for i, item in enumerate(items):
            image_url = item.get('image_url')
            if image_url:
                # Используем номер выпуска для имени файла, если он есть, иначе - индекс
                number = item.get('number', '').replace('/', '-')
                filename = f"cover_{year}_{number}_{i}.jpg"
                filepath = os.path.join(images_dir, filename)
                
                if download_image(image_url, filepath):
                    downloaded_count += 1
                time.sleep(0.1) # Небольшая задержка

    print(f"Скачивание завершено. Скачано {downloaded_count} из {total_images} изображений.")

def load_pdf_links(filename="links.csv"):
    """Загружает ссылки на PDF из CSV-файла."""
    links = {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                number = row.get('Выпуск', '').strip()
                pdf_url = row.get('Ссылка на выпуск', '').strip()
                if number and pdf_url:
                    links[number] = pdf_url
                    print(f"Добавлена ссылка для номера: {number} - {pdf_url}")
                else:
                    print(f"Пропущена строка с неполными данными: {row}")
        print(f"Загружено {len(links)} ссылок из {filename}")
    except FileNotFoundError:
        print(f"Файл {filename} не найден. Ссылки на PDF не будут добавлены.")
    return links

if __name__ == "__main__":
    print("Извлечение данных с помощью Selenium...")
    data = extract_with_selenium()
    pdf_links = load_pdf_links()

    if data:
        total_covers = sum(len(items) for items in data.values())
        print(f"Обработано {total_covers} обложек")
        generate_html_from_data(data, pdf_links, filename="index.html")
    else:
        print("Не удалось извлечь данные")
