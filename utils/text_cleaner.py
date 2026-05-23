import re
import html


def clean_html(text: str | None) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_salary_numbers(text: str | None) -> tuple[int | None, int | None]:
    if not text:
        return None, None
    nums = [int(n.replace(" ", "")) for n in re.findall(r"[\d ]{2,}", text) if n.strip()]
    nums = [n for n in nums if n > 1000]
    if not nums:
        return None, None
    return min(nums), max(nums)
