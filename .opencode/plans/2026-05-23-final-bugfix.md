# Final Bugfix Plan — 9 remaining bugs

## Task 1: Fix corrupted Russian text (HIGH)

**File:** `bot/keyboards.py:361, 367`

Replace garbled `"Р"Р°Р»РµРµ в†'"` with correct `"Далее →"` in:
1. `build_keywords_keyboard` (line ~361)
2. `build_exclude_keywords_keyboard` (line ~367)

Verify with: `python -c "with open('bot/keyboards.py','r',encoding='utf-8') as f: c=f.read(); assert 'Далее' in c"`

---

## Task 2: Re-render keyboard on keyword toggle (MEDIUM)

**File:** `bot/handlers/filters.py:102-113`

In `on_keyword_toggle`, after updating FSM state, re-render the current group keyboard:
```python
current_group = data.get("current_group")
if current_group:
    await _safe_edit(callback.message, reply_markup=build_keywords_for_group_keyboard(current_group, selected))
```
Also store `current_group` in `on_keyword_group_select`:
```python
await state.update_data(current_group=group)
```

---

## Task 3: Fix Trudvsem salary ValueError (MEDIUM)

**File:** `scrapers/trudvsem_ru.py:53`

Wrap `int(smin)` and `int(smax)` in try/except for the display text construction:
```python
try:
    smin_int = int(smin) if smin else None
    smax_int = int(smax) if smax else None
except (ValueError, TypeError):
    smin_int = smax_int = None
if (smin_int and smin_int != 0) or (smax_int and smax_int != 0):
```

---

## Task 4: Fix "без опыта" false positive (LOW)

**Files:** `scrapers/rabota_ru.py:149`, `scrapers/habr_career.py:127`

Only return "no" if no year numbers follow:
```python
if "без опыта" in text_lower:
    if not re.search(r'\d+\s*(?:года|лет|год)', text_lower):
        return "no"
```

---

## Task 5: Paginate rabota.ru (LOW)

**File:** `scrapers/rabota_ru.py:24`

Change `range(1)` to `range(3)`.

---

## Task 6: Fix duplicate messages on check_now (LOW)

**File:** `bot/handlers/control.py:243-255`

Use `_safe_edit` instead of `callback.message.answer()`:
```python
await _safe_edit(callback.message, text="✅ Проверка запущена!",
    reply_markup=build_start_keyboard())
```

---

## Task 7: Remove dead code (LOW)

**File:** `bot/keyboards.py:357-361`

Remove unused `build_keywords_keyboard` function.

---

## Task 8: Add state filter to keyword_toggle (LOW)

**File:** `bot/handlers/filters.py:101`

Add `FilterWizard.keywords` as the allowed state.

---

## Task 9: Remove unused EXPERIENCE_DONE enum (LOW)

**File:** `bot/keyboards.py:17`

Remove line `EXPERIENCE_DONE = "exp_done"`.

---

## Verification
- `pytest -v` — 33/33 pass
- `npm run build` — success
