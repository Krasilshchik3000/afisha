import os
from PIL import Image

def create_directory(dir_name):
    """Создает директорию, если она не существует."""
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
        print(f"Директория '{dir_name}' создана.")

def process_images(source_dir, target_dir, target_width=600, quality=85):
    """
    Изменяет размер и сжимает изображения.
    """
    create_directory(target_dir)
    
    files = [f for f in os.listdir(source_dir) if f.endswith('.jpg')]
    total_files = len(files)
    
    print(f"Начинаю обработку {total_files} изображений...")

    for i, filename in enumerate(files):
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)
        
        print(f"({i+1}/{total_files}) Обработка: {filename}", end="")

        try:
            with Image.open(source_path) as img:
                if img.mode in ('CMYK', 'P'):
                    img = img.convert('RGB')
                
                # Изменение размера с сохранением пропорций
                w_percent = (target_width / float(img.size[0]))
                h_size = int((float(img.size[1]) * float(w_percent)))
                img = img.resize((target_width, h_size), Image.Resampling.LANCZOS)

                img.save(target_path, format="JPEG", quality=quality, optimize=True)
                
                final_size_kb = os.path.getsize(target_path) / 1024
                print(f" -> сохранено ({final_size_kb:.1f} KB)")

        except Exception as e:
            print(f"\n  Ошибка обработки {filename}: {e}")
            
    print("Обработка завершена.")

if __name__ == "__main__":
    process_images(source_dir="covers_big", target_dir="covers_medium")
