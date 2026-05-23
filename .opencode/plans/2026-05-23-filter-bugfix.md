# Filter Bugfix Plan — Critical logic errors in filtering

**Goal:** Fix filter logic that passes vacancies with missing data. Fix scrapers to provide missing fields.

---

## Task 1: Fix `_process_vacancy` filter logic (3 critical bugs)

**File:** `core/scheduler.py:239-251`

### 1.1 Employment type filter (line 239)
```python
# BAD: vac_data.employment_type=None → short-circuits → passes everything
if emp_types and vac_data.employment_type and vac_data.employment_type not in emp_types:
    return
# FIX:
if emp_types:
    if not vac_data.employment_type or vac_data.employment_type not in emp_types:
        return
```

### 1.2 City filter (line 241)
```python
# BAD: vac_data.city=None → short-circuits → passes everything
if vf.city:
    city_label = CITIES.get(vf.city, vf.city).lower()
    if vac_data.city and city_label not in vac_data.city.lower():
        return
# FIX:
if vf.city:
    city_label = CITIES.get(vf.city, vf.city).lower()
    if not vac_data.city or city_label not in vac_data.city.lower():
        return
```

### 1.3 Experience filter (line 245)
```python
# BAD: vac_data.experience=None → short-circuits → passes everything
if experience and vac_data.experience and vac_data.experience != experience:
    return
# FIX:
if experience:
    if not vac_data.experience or vac_data.experience != experience:
        return
```

### 1.4 Salary filter (line 247) — conservative fix
```python
if vf.salary_min is not None or vf.salary_max is not None:
    if vf.salary_min is not None and vac_data.salary_max is not None and vac_data.salary_max < vf.salary_min:
        return
    if vf.salary_max is not None and vac_data.salary_min is not None and vac_data.salary_min > vf.salary_max:
        return
    # Added: when only one side is known, check the known side against vacancy
    if vf.salary_min is not None and vac_data.salary_min is not None and vac_data.salary_max is None and vac_data.salary_min < vf.salary_min:
        return  # vacancy min is below filter min, unknown max — can't confirm
    if vf.salary_max is not None and vac_data.salary_max is not None and vac_data.salary_min is None and vac_data.salary_max > vf.salary_max:
        return  # vacancy max is above filter max, unknown min — can't confirm
```

---

## Task 2: Fix trudvsem scraper

**File:** `scrapers/trudvsem_ru.py`

### 2.1 Convert salary 0 to None (consistency with hh/superjob)
```python
try:
    sal_min_val = int(smin) if smin else None
    sal_max_val = int(smax) if smax else None
    if sal_min_val == 0: sal_min_val = None
    if sal_max_val == 0: sal_max_val = None
except (ValueError, TypeError):
    sal_min_val = None
    sal_max_val = None
```

### 2.2 Extract experience from API
The trudvsem API has `minExperience` and `maxExperience` fields (in months).
```python
# Read the raw value from the vacancy object:
min_exp = v.get("minExperience")
if min_exp is not None:
    exp_months = int(min_exp)
    if exp_months <= 0:
        exp_value = "no"
    elif exp_months <= 12:
        exp_value = "1-3"
    elif exp_months <= 36:
        exp_value = "3-6"
    else:
        exp_value = "6+"
```

---

## Task 3: Fix rabota.ru scraper

**File:** `scrapers/rabota_ru.py`

### 3.1 Extract salary_min/max from salary_text
Using existing `extract_salary_numbers` from `utils/text_cleaner.py`:
```python
from utils.text_cleaner import extract_salary_numbers
# After salary_text is set:
salary_min, salary_max = extract_salary_numbers(salary_text) if salary_text else (None, None)
```

### 3.2 Add experience detection from card text
```python
exp_value = None
if card:
    card_text = card.get_text(" ", strip=True).lower()
    if "без опыта" in card_text or "без опыта работы" in card_text:
        exp_value = "no"
    elif "опыт" in card_text:
        import re
        exp_years = re.findall(r'от\s*(\d+)\s*(?:года|лет|год)', card_text)
        if exp_years:
            years = int(exp_years[0])
            if years <= 1: exp_value = "1-3"
            elif years <= 3: exp_value = "3-6"
            else: exp_value = "6+"
```

---

## Task 4: Fix habr career scraper

**File:** `scrapers/habr_career.py`

### 4.1 Extract salary_min/max from salary_text
Same approach as rabota.ru — use `extract_salary_numbers`.

### 4.2 Extract experience from card
```python
exp_value = None
exp_el = card.select_one("[class*=experience]") or card.select_one("[class*=exp-]")
if exp_el:
    exp_text = exp_el.get_text(strip=True).lower()
    if "без опыта" in exp_text:
        exp_value = "no"
    elif "1–3" in exp_text or "1-3" in exp_text:
        exp_value = "1-3"
    elif "3–6" in exp_text:
        exp_value = "3-6"
    elif "6" in exp_text:
        exp_value = "6+"
```

---

## Verification

- [ ] `pytest -v` — 33/33 pass
- [ ] `npm run build` — frontend builds
