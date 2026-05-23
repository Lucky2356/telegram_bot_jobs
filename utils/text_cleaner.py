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
    nums = [int(n.replace(" ", "")) for n in re.findall(r"\d[\d ]*", text) if n.strip()]
    nums = [n for n in nums if n > 1000]
    if not nums:
        return None, None
    if len(nums) == 1:
        val = nums[0]
        text_lower = text.lower()
        if "до" in text_lower and "от" not in text_lower:
            return (None, val)
        elif "от" in text_lower and "до" not in text_lower:
            return (val, None)
        return (val, val)
    return min(nums), max(nums)
