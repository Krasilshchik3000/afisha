#!/usr/bin/env python3
import csv
import json
from bs4 import BeautifulSoup

def load_csv_data():
    """Загружает данные из links.csv"""
    csv_data = {}
    with open('links.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row['Дата']}_{row['Выпуск']}"
            csv_data[key] = {
                'pdf_url': row['Ссылка на выпуск'],
                'cover_url': row['Ссылка на обложку']
            }
    return csv_data

def load_html_data():
    """Загружает данные из index_selenium.html"""
    with open('index_selenium.html', 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    html_data = []
    covers = soup.find_all('div', class_='cover-item')

    for cover in covers:
        number_elem = cover.find('div', class_='cover-number')
        date_elem = cover.find('div', class_='cover-date')
        img_elem = cover.find('img')

        if number_elem and date_elem and img_elem:
            number = number_elem.get_text(strip=True)
            date = date_elem.get_text(strip=True)
            img_url = img_elem.get('src', '')

            html_data.append({
                'number': number,
                'date': date,
                'image_url': img_url,
                'key': f"{date}_{number}"
            })

    return html_data

def merge_data():
    """Объединяет данные из HTML и CSV"""
    csv_data = load_csv_data()
    html_data = load_html_data()

    merged_data = {}

    for item in html_data:
        key = item['key']
        if key in csv_data:
            item.update(csv_data[key])
            # Извлекаем год из даты
            year = item['date'][:4]
            if year not in merged_data:
                merged_data[year] = []
            merged_data[year].append(item)

    # Сортируем данные внутри каждого года
    for year in merged_data:
        merged_data[year].sort(key=lambda x: x['date'])

    return merged_data

def generate_html_with_pdf(merged_data, filename="index_with_pdf.html"):
    """Генерирует HTML с поп-апами для PDF"""
    html_content = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Архив обложек журнала Афиша</title>
    <link rel="stylesheet" href="styles.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Grato+Grotesk:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Grato Grotesk', -apple-system, BlinkMacSystemFont, sans-serif; }

        /* Поп-ап стили */
        .pdf-modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.9);
            overflow: auto;
        }

        .pdf-modal-content {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 90%;
            max-width: 1200px;
            height: 90%;
            position: relative;
        }

        .pdf-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 15px;
            margin-bottom: 15px;
            border-bottom: 1px solid #e9ecef;
        }

        .pdf-modal-close {
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }

        .pdf-modal-close:hover {
            color: #000;
        }

        .pdf-container {
            width: 100%;
            height: calc(100% - 80px);
            border: none;
        }

        .pdf-info {
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 6px;
            font-size: 1.1rem;
            color: #495057;
        }

        .pdf-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            font-size: 1.2rem;
            color: #6c757d;
        }
    </style>
</head>
<body>
    <header>
        <h1>Архив обложек журнала Афиша</h1>
        <p>Коллекция обложек по годам</p>
    </header>

    <main>
"""

    for year in sorted(merged_data.keys()):
        html_content += f"""
        <section class="year-section">
            <h2 class="year-title">{year}</h2>
            <div class="covers-grid">
"""

        for item in merged_data[year]:
            pdf_url = item.get('pdf_url', '')
            if pdf_url:
                onclick = f"openPdfModal('{pdf_url}', '{item['number']} - {item['date']}')"
            else:
                onclick = ""

            html_content += f"""
                <div class="cover-item" onclick="{onclick}" style="{'cursor: pointer;' if pdf_url else ''}">
                    <div class="cover-image">
                        <img src="{item['image_url']}" alt="Обложка {item['number']}" loading="lazy">
                    </div>
                    <div class="cover-info">
                        <div class="cover-number">{item['number']}</div>
                        <div class="cover-date">{item['date']}</div>
                    </div>
                </div>
"""

        html_content += """
            </div>
        </section>
"""

    html_content += """
    </main>

    <!-- Поп-ап для PDF -->
    <div id="pdfModal" class="pdf-modal">
        <div class="pdf-modal-content">
            <div class="pdf-modal-header">
                <div class="pdf-info" id="pdfInfo">Загрузка...</div>
                <span class="pdf-modal-close" onclick="closePdfModal()">&times;</span>
            </div>
            <iframe id="pdfFrame" class="pdf-container" src="" frameborder="0"></iframe>
        </div>
    </div>

    <script>
        function openPdfModal(pdfUrl, infoText) {
            document.getElementById('pdfInfo').textContent = infoText;
            document.getElementById('pdfFrame').src = pdfUrl;
            document.getElementById('pdfModal').style.display = 'block';
            document.body.style.overflow = 'hidden'; // Запрещаем прокрутку фона
        }

        function closePdfModal() {
            document.getElementById('pdfModal').style.display = 'none';
            document.getElementById('pdfFrame').src = '';
            document.body.style.overflow = 'auto'; // Разрешаем прокрутку фона
        }

        // Закрываем поп-ап при клике вне его области
        window.onclick = function(event) {
            const modal = document.getElementById('pdfModal');
            if (event.target === modal) {
                closePdfModal();
            }
        }

        // Закрываем поп-ап при нажатии Escape
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closePdfModal();
            }
        });
    </script>
</body>
</html>
"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML страница с поп-апами создана: {filename}")

if __name__ == "__main__":
    print("Объединение данных из HTML и CSV...")
    merged_data = merge_data()
    generate_html_with_pdf(merged_data)
    print(f"Обработано {sum(len(items) for items in merged_data.values())} обложек с PDF")
