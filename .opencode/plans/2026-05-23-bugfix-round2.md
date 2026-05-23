# Bugfix Round 2 — Telegram keyboard + Sidebar layout + Overflow

**Goal:** Fix three remaining core issues: keyword keyboard UX, sidebar jumping, and overflow

---

## Task 1: Telegram — Two-step keyword selection

**Why:** 92 keywords in one keyboard causes scroll reset on every toggle (iOS Telegram). Even with "Далее" at top, UX is broken.

**How:** Split selection into 2 screens:
1. **Step A** — Show 15 group buttons (compact: 5 rows of 3)
2. **Step B** — Show keywords for selected group (5-10 per group, 1-3 rows)
3. No `edit_reply_markup` on toggle — answer callback only
4. Keyboard only rebuilds on "Back to groups" or group change

**Files:**
- Modify: `bot/keyboards.py` — new builders
- Modify: `bot/handlers/filters.py` — new state + handlers
- No new files

**States in FSM:**
- `FilterWizard.keyword_groups` — shows group list
- `FilterWizard.keywords` — shows keywords for selected group (reuses existing)

**Implementation:**

- [ ] **Step 1: Add group-related WizardAction values**
  ```python
  class WizardAction(StrEnum):
      ...
      KW_GROUP_SELECT = "kwg"   # New: select a group
      KW_GROUP_BACK = "kwg_bk"  # New: back to groups
  ```

- [ ] **Step 2: Build `build_keyword_groups_keyboard()`**
  ```python
  def build_keyword_groups_keyboard() -> InlineKeyboardMarkup:
      builder = InlineKeyboardBuilder()
      for group_name in KEYWORDS_BY_GROUP:
          builder.row(InlineKeyboardButton(
              text=group_name,
              callback_data=FilterCallback(action=WizardAction.KW_GROUP_SELECT, value=group_name).pack(),
          ))
      builder.row(_btn("✅ Далее →", WizardAction.KEYWORD_DONE))
      builder.row(_btn("❌ Отмена", WizardAction.CANCEL))
      return builder.as_markup()
  ```

- [ ] **Step 3: Build `build_keywords_in_group_keyboard(group, selected)`**
  - Shows keywords for ONE group only
  - Rows of 4, same visual style as current (✅ for selected)
  - Has "⬅️ Назад к группам" + "✅ Далее →" at top AND bottom
  - Does NOT re-render on toggle — preserves scroll

- [ ] **Step 4: Modify `on_keyword_toggle` handler**
  - Answer callback immediately: `await callback.answer("✅ " + kw if adding else "🚫 " + kw)`
  - Update FSM state
  - Do NOT edit message — no re-render, no scroll reset
  - User sees visual feedback via toast/answer

- [ ] **Step 5: Add `on_keyword_group_select` handler**
  - Reads selected keywords from state
  - Shows keywords for selected group via `_safe_edit`
  - Sets `FilterWizard.keywords` state

- [ ] **Step 6: Modify `on_keyword_done` to proceed regardless of FSM state name**
  - Keep validation: `if not selected: callback.answer(...)`

- [ ] **Step 7: Commit**
  ```bash
  git add bot/ && git commit -m "fix(bot): two-step keyword selection to avoid scroll reset on toggle"
  ```

---

## Task 2: Sidebar — stop layout jump on content load

**Why:** Sidebar stretches with main content because `flex-col` has no fixed height. Theme toggle jumps down when content loads.

**Fix:**
- `sticky top-0 h-screen` on `<aside>`
- `overflow-y-auto` on tabs area
- `mt-auto` on bottom section

- [ ] **Step 1: Fix sidebar classes**
  ```tsx
  // Before (App.tsx:211):
  <aside className="hidden md:flex flex-col w-48 lg:w-56 shrink-0 border-r ...">
  // After:
  <aside className="hidden md:flex flex-col w-48 lg:w-56 shrink-0 border-r ... sticky top-0 h-screen">
  ```

- [ ] **Step 2: Fix bottom section**
  ```tsx
  // Before (App.tsx:218):
  <div className="p-3 border-t ...">
  // After:
  <div className="p-3 border-t ... mt-auto">
  ```

- [ ] **Step 3: Commit**
  ```bash
  git add web/frontend/src/App.tsx && git commit -m "fix(web): fix sidebar layout shift with sticky + h-screen + mt-auto"
  ```

---

## Task 3: Full overflow audit

**What to check in every component:**
- Any `flex` row without `flex-wrap` that could overflow on small screens
- Any fixed width that doesn't scale
- Missing `truncate` or `break-words` on text
- Missing `min-w-0` on flex children
- `overflow-x-auto` where horizontal scroll should be allowed

- [ ] **Step 1: Check each component systematically**
  Read each file and check for overflow patterns.

- [ ] **Step 2: Fix issues found**
  - Apply `flex-wrap`, `truncate`, `break-all`, `min-w-0`, `overflow-hidden`

- [ ] **Step 3: Commit**
  ```bash
  git add web/frontend/src/components/ && git commit -m "fix(web): fix overflow across all components"
  ```

---

## Verification

- [ ] **pytest**: 21/21 passed
- [ ] **Frontend build**: `npm run build` succeeds
