import re

with open("bot/handlers/filters.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace "Шаг N — Текст" with just "Текст"
content = re.sub(r'Шаг \d+ — ', "", content)

with open("bot/handlers/filters.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Step numbers removed")
