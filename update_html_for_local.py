#!/usr/bin/env python3
import os
import re
from bs4 import BeautifulSoup

def update_html_with_local_images():
    """Обновляет HTML файл для использования локальных изображений"""
    with open('index_selenium.html', 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Получаем все элементы изображений
    img_tags = soup.find_all('img')

    # Получаем список файлов в папке covers
    covers_dir = 'covers'
    cover_files = sorted(os.listdir(covers_dir)) if os.path.exists(covers_dir) else []

    print(f"Найдено {len(cover_files)} локальных изображений")
    print(f"Найдено {len(img_tags)} элементов изображений в HTML")

    # Создаем словарь для сопоставления номеров журналов с файлами
    # Ключ: номер журнала из alt атрибута, значение: соответствующий файл
    issue_to_file = {}

    for file in cover_files:
        # Извлекаем номер журнала из названия файла
        # Формат: cover_Год_№ Номер (Дополнительно)_Индекс.jpg
        # Например: cover_1999_№ 1 (1)_0.jpg -> № 1 (1)
        match = re.search(r'№\s*([^_]+)', file)
        if match:
            issue_number = match.group(1).strip()
            issue_to_file[issue_number] = file
            print(f"Файл {file} соответствует номеру: {issue_number}")

    # Обновляем src атрибуты, сопоставляя номера журналов
    updated_count = 0
    for img_tag in img_tags:
        alt_text = img_tag.get('alt', '')
        if 'Обложка' in alt_text:
            # Извлекаем номер журнала из alt текста
            # Формат: Обложка № 1 (1)
            match = re.search(r'Обложка\s+№\s*([^"]+)', alt_text)
            if match:
                issue_number = match.group(1).strip()
                if issue_number in issue_to_file:
                    correct_file = issue_to_file[issue_number]
                    old_src = img_tag.get('src', '')
                    new_src = f"covers/{correct_file}"
                    img_tag['src'] = new_src
                    updated_count += 1
                    print(f"Обновлено: {alt_text} -> {new_src} (было: {old_src})")
                else:
                    print(f"Предупреждение: не найден файл для номера {issue_number}")

    print(f"Обновлено {updated_count} изображений")

    # Сохраняем обновленный HTML
    with open('index_selenium.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))

    print("HTML файл обновлен для использования локальных изображений")

if __name__ == "__main__":
    update_html_with_local_images()
