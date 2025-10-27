#!/usr/bin/env python3
"""
Извлекает 90-ю страницу из PDF для обложки №6 (77) 2002 года
"""
import requests
from pdf2image import convert_from_bytes
from PIL import Image
import os

def download_and_extract_cover():
    # URL для PDF №6 (77) 2002 года
    pdf_url = "https://archivarius-public.s3.us-west-2.amazonaws.com/rima/print/scraped_printed_issue/1469/issue.pdf"
    
    print(f"Скачиваю PDF: {pdf_url}")
    
    try:
        # Скачиваем PDF
        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()
        
        print("Преобразую страницу 90 в изображение...")
        
        # Извлекаем страницу 90 (индекс 89)
        images = convert_from_bytes(response.content, first_page=90, last_page=90, dpi=200)
        
        if images:
            # Берем только левую половину разворота
            img = images[0]
            width, height = img.size
            
            # Левая половина
            left_half = img.crop((0, 0, width // 2, height))
            
            # Масштабируем до размера 600x848 (как другие обложки в covers_medium)
            left_half_resized = left_half.resize((600, 848), Image.Resampling.LANCZOS)
            
            # Сохраняем
            output_path = "covers_medium/cover_2002_N_6_77_0.jpg"
            left_half_resized.save(output_path, "JPEG", quality=85)
            
            print(f"✅ Сохранено: {output_path}")
            print(f"   Размер: {left_half_resized.size}")
            
        else:
            print("⚠️ Не удалось извлечь страницу")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    download_and_extract_cover()
