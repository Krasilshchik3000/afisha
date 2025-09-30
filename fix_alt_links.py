#!/usr/bin/env python3
import re
from bs4 import BeautifulSoup

def fix_pdf_links():
    """Заменяет ссылки target="_blank" на вызов функции openPdfModal"""
    with open('index_alt.html', 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Находим все элементы a с target="_blank" и href на PDF
    for a_tag in soup.find_all('a', href=True):
        href = a_tag.get('href', '')
        if 'target="_blank"' in str(a_tag) and href.endswith('.pdf'):
            # Извлекаем номер журнала из alt текста изображения внутри ссылки
            img_tag = a_tag.find('img')
            if img_tag and img_tag.get('alt'):
                alt_text = img_tag['alt']
                # Извлекаем номер из alt текста (формат: "Обложка № 1 (1)")
                match = re.search(r'№\s*([^"]+)', alt_text)
                if match:
                    issue_number = match.group(1).strip()
                    # Находим номер журнала в cover-number элементе
                    cover_info = a_tag.find_next_sibling('div', class_='cover-info')
                    if cover_info:
                        cover_number_elem = cover_info.find('div', class_='cover-number')
                        cover_date_elem = cover_info.find('div', class_='cover-date')
                        if cover_number_elem and cover_date_elem:
                            full_number = cover_number_elem.get_text(strip=True)
                            date = cover_date_elem.get_text(strip=True)
                            info_text = f"{full_number} - {date}"

                            # Заменяем href и target на onclick
                            a_tag['href'] = '#'
                            a_tag['onclick'] = f"openPdfModal('{href}', '{info_text}')"
                            # Удаляем target="_blank"
                            if 'target' in a_tag.attrs:
                                del a_tag['target']

                            print(f"Обновлено: {alt_text} -> onclick с PDF {href}")

    # Сохраняем обновленный HTML
    with open('index_alt.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))

    print("Все ссылки обновлены")

if __name__ == "__main__":
    fix_pdf_links()
