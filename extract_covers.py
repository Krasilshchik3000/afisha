import os
import csv
import requests
import fitz  # PyMuPDF
from collections import defaultdict
from datetime import datetime

def create_output_directory(dir_name="covers_big"):
    """Создает директорию, если она не существует."""
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
        print(f"Директория '{dir_name}' создана.")

def load_links(filename="links.csv"):
    """Загружает данные из CSV и группирует по годам."""
    data_by_year = defaultdict(list)
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date_str = row.get('Дата')
                if date_str:
                    year = datetime.strptime(date_str, '%Y-%m-%d').year
                    data_by_year[str(year)].append(row)
        print(f"Загружены данные из {filename}.")
    except FileNotFoundError:
        print(f"Ошибка: Файл {filename} не найден.")
        return None
    return data_by_year

def sanitize_filename(name):
    """Очищает имя файла от недопустимых символов."""
    return name.replace('/', '-').replace('\\', '-')

def extract_covers():
    """Основная функция для извлечения обложек."""
    output_dir = "covers_big"
    create_output_directory(output_dir)
    data_by_year = load_links()

    if not data_by_year:
        return

    total_links = sum(len(items) for items in data_by_year.values())
    processed_count = 0

    print(f"Начинаю обработку {total_links} PDF-файлов...")

    for year in sorted(data_by_year.keys()):
        # Сортируем выпуски по дате, чтобы индекс 'i' совпадал с предыдущей логикой
        sorted_items = sorted(data_by_year[year], key=lambda x: x['Дата'])
        
        for i, row in enumerate(sorted_items):
            issue_number = row.get('Выпуск')
            pdf_url = row.get('Ссылка на выпуск')
            
            if not (issue_number and pdf_url):
                continue

            sanitized_number = sanitize_filename(issue_number)
            new_filename = f"cover_{year}_{sanitized_number}_{i}.jpg"
            output_path = os.path.join(output_dir, new_filename)

            processed_count += 1
            print(f"({processed_count}/{total_links}) Обработка: {new_filename}")

            try:
                # 1. Скачиваем PDF
                response = requests.get(pdf_url, timeout=60)
                response.raise_for_status()
                pdf_bytes = response.content

                # 2. Открываем PDF из памяти
                pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                
                # 3. Извлекаем первую страницу
                first_page = pdf_doc.load_page(0)
                
                # 4. Конвертируем в изображение с высоким разрешением
                pix = first_page.get_pixmap(dpi=300)
                
                # 5. Сохраняем как JPEG
                pix.save(output_path, "jpeg")

                pdf_doc.close()

            except requests.exceptions.RequestException as e:
                print(f"  Ошибка скачивания {pdf_url}: {e}")
            except Exception as e:
                print(f"  Ошибка обработки файла для {issue_number}: {e}")

    print("Обработка завершена.")

if __name__ == "__main__":
    extract_covers()
