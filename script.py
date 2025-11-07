import os
import pandas as pd

def process_all_files_silent(directory):
    """
    Обрабатывает все файлы без лишних сообщений
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            
            try:
                df = pd.read_csv(file_path, sep=';', header=None)
                df = df.iloc[:, :2]
                df.columns = ['X', 'Y']
                df.to_csv(file_path, sep='\t', index=False)
                print(f"✓ {file_path}")
            except:
                print(f"✗ {file_path}")

# Использование
if __name__ == "__main__":
    folder_path = input("Введите путь к папке: ").strip()
    process_all_files_silent(folder_path)
    print("Готово!")