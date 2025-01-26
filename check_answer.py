import re
from nltk.stem.snowball import SnowballStemmer

short_words = [
    # Предлоги
    "в", "к", "с", "у", "о", "а", "и", "на", "по", "под", "над", "за", "до", "об", "из", "от", "без", "про",
    # Частицы
    "не", "ни"
]


def remove_trailing_vowels(word):
    result = re.sub(r'[аеёиоуыэюяьй]+$', '', word)
    return result if result else word


def is_one_char_diff(word1, word2):
    if abs(len(word1) - len(word2)) > 1:
        return False
    if len(word1) != len(word2):
        short, long = (word1, word2) if len(word1) < len(word2) else (word2, word1)
        for i in range(len(long)):
            if short == long[:i] + long[i + 1:]:
                return True
    if len(word1) == len(word2):
        diff_count = sum(1 for a, b in zip(word1, word2) if a != b)
        return diff_count == 1
    return False


def check_strings(first: str, second: str) -> int:
    second = second.replace("Ответ: ", "").lower().strip()
    second = re.sub(r"комментарий:.*", "", second, flags=re.DOTALL).strip()
    first_words = re.findall(r'\b\w+\b', first.lower())
    second_words = re.findall(r'\b\w+\b', second.lower())

    if len(second_words) > 1:
        for word in short_words:
            if word in second_words:
                second_words.remove(word)

    stemmer = SnowballStemmer("russian")
    roots1 = {stemmer.stem(word) for word in first_words}
    roots2 = {stemmer.stem(word) for word in second_words}

    matches = 0
    for root2 in roots2:
        for root1 in roots1:
            if root2 == root1 or (len(root2) > 5 and is_one_char_diff(root1, root2)):
                matches += 1
                break
    if matches == len(roots2):
        return 2
    elif matches > 0:
        return 1

    for root2 in roots2:
        for root1 in roots1:
            if len(root2) > 3 and root2 in root1:
                return 1
    return 0

# Тестовые данные
# test_cases = [
#     ("в доме", "дом", 2),  # Совпадает корень слова
#     ("внутри здания", "здание", 2),  # Совпадает корень слова с предлогом
#     ("на столе", "стол", 2),  # Совпадает корень слова
#     ("за окном", "окно", 2),  # Совпадает корень слова
#     ("на крыше", "крыша", 2),  # Совпадает корень
#     ("у дерева", "деревья", 2),  # Различие в одном символе
#     ("под мостом", "мост", 2),  # Слово в середине
#     ("в квартире", "доме", 0),  # Нет совпадения
#     ("на стене", "окно", 0),  # Нет совпадения
#     ("в лесу", "вода", 0),  # Нет совпадения
#     ("меж деревьев", "лес", 0),  # Разные корни
#     ("лишь случай", "случайность", 1),  # Совпадение по корню
#     ("крысиный король", "именем короля", 1),
#     ("золотодобыча", "золотых песков", 1),
#     ("грекоримская", "греко-римская", 1),
#     ("большой мозг", "большой апельсин", 1),
#     ("царский двор", "шотландский двор", 1),
#     ("альбом для марок", "коллекция марок", 1),
#     ("казней египетских", "тьма египетская", 1),
#     ("атомная энергетика", "энергосберегающая лампочка", 0),
#     ("над горой", "над столом", 1),
#     ("надежн горой", "надежным столом", 1),
#     ("рог", "удаление рога", 1),
#     ("Море в Мекке", "мертвое море", 1),
#     ("тарзак", "тарзан", 1),
#     ("тарзан", "тарзан", 2),
#     ("Строительство землянки на берегу реки", "идущий к реке", 1)
#
# ]
#
# for first, second, expected in test_cases:
#     result = check_strings(first, second)
#     print(f"Строки: \"{first}\" и \"{second}\" -> {result}, ожидалось: {expected}")
