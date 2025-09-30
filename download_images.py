#!/usr/bin/env python3
import requests
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def extract_image_urls(url):
    """Извлекает все URL изображений из HTML страницы по указанному URL"""
    print(f"Загрузка HTML со страницы: {url}")
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    urls = []
    img_tags = soup.find_all('img')
    for img in img_tags:
        src = img.get('src', '')
        if src.startswith('https://lh3.googleusercontent.com/'):
            urls.append(src)

    return urls

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

def main():
    """Основная функция"""
    # Создаем папку для изображений
    images_dir = 'covers'
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # URL для скачивания
    sheet_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vT1R7dx12qHVZLlhM6Jm9sKo28_qVuMR1CLtU99woNx7LaqBp0UREiuQHSAZ-1oFgKzQXNQeKKy1Emy/pubhtml'

    # Извлекаем URL изображений
    print("Извлечение URL изображений...")
    image_urls = extract_image_urls(sheet_url)
    print(f"Найдено {len(image_urls)} изображений")

    # Скачиваем изображения
    downloaded = 0
    for i, url in enumerate(image_urls):
        # Создаем имя файла из URL
        parsed = urlparse(url)
        filename = os.path.join(images_dir, f"cover_{i+1}.jpg")

        if download_image(url, filename):
            downloaded += 1

        # Небольшая пауза между запросами
        import time
        time.sleep(0.5)

    print(f"Скачано {downloaded} из {len(image_urls)} изображений")


if __name__ == "__main__":
    main()
