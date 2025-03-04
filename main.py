import datetime
import telebot
import os
from PIL import Image
import cv2
import numpy as np

import find_digit


# Укажите здесь ваш токен от BotFather
token = "7363574414:AAHhw8Zl7_dHIQ70Q5OjLshwUwS_MIH9WEA"

# Папка для сохранения файлов
SAVE_FOLDER = "downloads"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Функция для записи данных сообщения в лог-файл
def log_message(message):
    log_entry = (
        f"Время: {datetime.datetime.now()}\n"
        f"ID сообщения: {message.message_id}\n"
        f"Текст: {message.text}\n"
        f"ID чата: {message.chat.id}\n"
        f"Имя пользователя: {message.from_user.first_name}\n"
        f"Фамилия пользователя: {message.from_user.last_name}\n"
        f"Логин пользователя: @{message.from_user.username}\n"
    )

    # Если сообщение содержит файл
    if message.document:
        log_entry += f"Имя файла: {message.document.file_name}\n"

    # Если сообщение содержит фото
    if message.photo:
        # Получаем самое большое фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = os.path.join(SAVE_FOLDER, f"photo_{message.message_id}.jpg")
        with open(file_name, "wb") as photo_file:
            photo_file.write(downloaded_file)
        log_entry += f"Фото сохранено как: {file_name}\n"
        handle_saved_photo(file_name, message)

    log_entry += "---\n"

    with open("message_log.txt", "a") as log_file:
        log_file.write(log_entry)

# Функция для поиска координат совпадений цифры на изображении
def find_digit_coordinates(main_image_path, digit_image_path):
    # Загружаем изображения
    main_image = cv2.imread(main_image_path, cv2.IMREAD_GRAYSCALE)
    digit_image = cv2.imread(digit_image_path, cv2.IMREAD_GRAYSCALE)

    # Применяем шаблонное совпадение
    result = cv2.matchTemplate(main_image, digit_image, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8  # Уровень совпадения для признания области подходящей
    locations = np.where(result >= threshold)

    # Преобразуем результаты в список координат верхнего левого угла
    coordinates = list(zip(locations[1], locations[0]))
    return coordinates

# Функция для извлечения судоку из изображения
def extract_sudoku_from_image(file_name):
    # Здесь должна быть реализация извлечения судоку из изображения
    # Пока вернём пример сетки для тестирования
    extracted_grid = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
    return extracted_grid

# Функция для решения судоку
def solve_sudoku(grid):
    # Пустая клетка обозначена как 0
    def is_valid(num, row, col):
        # Проверяем строку
        if num in grid[row]:
            return False

        # Проверяем колонку
        if num in [grid[i][col] for i in range(9)]:
            return False

        # Проверяем 3x3 квадрат
        start_row, start_col = 3 * (row // 3), 3 * (col // 3)
        for i in range(start_row, start_row + 3):
            for j in range(start_col, start_col + 3):
                if grid[i][j] == num:
                    return False

        return True

    def solve():
        for row in range(9):
            for col in range(9):
                if grid[row][col] == 0:
                    for num in range(1, 10):
                        if is_valid(num, row, col):
                            grid[row][col] = num
                            if solve():
                                return True
                            grid[row][col] = 0
                    return False
        return True

    solve()
    return grid


def handle_saved_photo(file_name, message):
    """
    Обрабатывает сохраненное фото, решает судоку и отправляет результат пользователю.
    """
    # Получаем размер изображения в пикселях
    with Image.open(file_name) as img:
        width, height = img.size

    # Проверяем размер изображения
    if width == 591 and height == 1280:
        # Извлекаем судоку из изображения
        sudoku_grid = find_digit.sudoku_image_to_array(file_name)

        # Решаем судоку
        solved_grid = solve_sudoku(sudoku_grid)
        bot.send_message(message.chat.id, "Судоку решено!")
        # Отправляем сердечко
        bot.send_message(message.chat.id, "😀️")

        # Накладываем решение на изображение
        find_digit.overlay_sudoku_solution(file_name, solved_grid)

        # Формируем имя выходного файла
        base_name, ext = os.path.splitext(file_name)
        solved_image_path = f"{base_name}_solved{ext}"

        # Отправляем обработанное изображение пользователю
        with open(solved_image_path, 'rb') as solved_image:
            bot.send_photo(message.chat.id, solved_image)


try:
    bot = telebot.TeleBot(token)
    print("Бот создан успешно")
except Exception as e:
    print(f"Ошибка при создании бота: {e}")

try:
    bot_info = bot.get_me()
    print(bot_info)
except Exception as e:
    print(f"Ошибка get_me: {e}")

@bot.message_handler(func = lambda message: True)
def handle_message(message):
    bot.reply_to(message, "Ваше сообщение прочитано!")
    # Сохраняем данные сообщения в лог-файл
    log_message(message)


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    print(f"ID файла: {message.photo[-1].file_id}")  # ID файла фото
    bot.reply_to(message, "Спасибо за фото!")
    # Сохраняем данные сообщения в лог-файл
    log_message(message)


while True:
    try:
        bot.infinity_polling(timeout = 10, long_polling_timeout = 5)
    except Exception as e:
        print(f"Ошибка bot.infinity_polling: {e}")

