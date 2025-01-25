from PIL import Image, ImageDraw, ImageFont

def create_question_image(question_text: str, question_id: int) -> str:
    """Создает изображение с текстом вопроса, выравненным по левому краю, и обрезает пустую часть."""
    # Настройки изображения
    img_width, img_height = 800, 1600
    bg_color = (255, 255, 255)
    text_color = (0, 0, 0)
    font_path = "arial.ttf"  # Убедитесь, что шрифт доступен
    font_size = 25
    padding = 20  # Отступ от краев изображения

    # Создаем изображение
    image = Image.new("RGB", (img_width, img_height), color=bg_color)
    draw = ImageDraw.Draw(image)

    # Загружаем шрифт
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        raise Exception(f"Не удалось загрузить шрифт: {font_path}")

    # Форматируем текст, учитывая переносы строк
    lines = []
    for line in question_text.split('\n'):  # Учитываем переносы строк в тексте
        words = line.split()
        temp_line = ""
        for word in words:
            test_line = f"{temp_line} {word}".strip()
            text_bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            if text_width <= img_width - 2 * padding:  # Учитываем отступы
                temp_line = test_line
            else:
                lines.append(temp_line)
                temp_line = word
        if temp_line:
            lines.append(temp_line)

    # Отрисовываем текст на изображении (выравнивание по левому краю)
    y_offset = padding
    max_y = 0
    for line in lines:
        draw.text((padding, y_offset), line, font=font, fill=text_color)  # x = padding для левого края
        text_bbox = draw.textbbox((0, 0), line, font=font)
        text_height = text_bbox[3] - text_bbox[1]
        y_offset += text_height + 10
        max_y = y_offset

    # Обрезка изображения
    cropped_image = image.crop((0, 0, img_width, max(400, max_y + padding)))

    # Сохраняем изображение
    image_path = f"questions_images/question_{question_id}.png"
    cropped_image.save(image_path)
    return image_path