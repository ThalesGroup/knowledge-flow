# 🧑‍💻 Fred Backend Python Development Guide

> 📌 All developers MUST follow this guide when working on Python backend code in the Fred or KnowledgeFlow backend repositories.

Fred is a professional open-source agentic platform. Even if you're junior, **you are writing production code**. That means others will reuse, debug, extend, and rely on your modules.

This guide ensures:
- ✅ Consistent code style across controllers, services, agents
- ✅ Robust exception handling
- ✅ Easier testing and maintenance
- ✅ Less spaghetti, more stability

---

## 🧱 Project Structure Principles

- All **external APIs** go in `controller/` modules.
- All **business logic** goes in `services/`.
- All **reusable logic** goes in `common/` or `utils/`.
- All **models** must be defined using **Pydantic** and reused across layers.

> ✅ Every route in a controller should delegate **all logic** to a `Service` class.

---

## 🧨 Exception Handling: Mandatory Best Practices

### ✅ Always raise **Business Exceptions** from services

```python
# GOOD (in service)
raise ProfileNotFound("Chat profile does not exist")
```

```python
# BAD (in controller)
raise HTTPException(404, "Not found")
```

> The controller is responsible for turning business exceptions into HTTP errors.

---

### ✅ Centralize your exception types

All exception types must live in:

```
knowledge_flow_app/common/business_exception.py
```

Use subclasses:

```python
class ChatProfileError(BusinessException): ...
class ProfileNotFound(ChatProfileError): ...
class TokenLimitExceeded(ChatProfileError): ...
```

---

### ✅ Use `log_exception(e, context)` for unexpected errors

```python
except Exception as e:
    log_exception(e, "while updating profile")
    raise ChatProfileError("Internal error")
```

This ensures:
- Logs have full traceback
- Caller sees a clean message
- We never swallow bugs

---

## 🧼 Utility Code: Clean, Reusable, Documented

- All utility functions live in `common/utils.py`.
- Every function must be documented with:
  - Purpose
  - Parameters
  - Returns
  - Example (if useful)

Example:

```python
def utc_now_iso() -> str:
    """
    Returns current UTC time in ISO 8601 format.
    Used for `created_at`, `updated_at` fields across the app.

    Returns:
        str: UTC timestamp like '2025-06-21T10:15:00+00:00'
    """
    ...
```

---

## 💡 Services: Clear, Stateless, Robust

- No business logic should be in the controller
- Never mix filesystem operations with metadata logic
- Use Pydantic types throughout (e.g. `ChatProfile`, `ChatProfileDocument`)

### Example Method Signature

```python
async def update_profile(
    self,
    profile_id: str,
    title: str,
    description: str,
    files: list[UploadFile]
) -> ChatProfile
```

---

## 🔌 Controllers: Thin & Declarative

A controller must:
- Only call service methods
- Catch and translate known exceptions to `HTTPException`
- Use `Form(...)` and `File(...)` explicitly

### Example

```python
@router.post("/chatProfiles")
async def create_profile(
    title: str = Form(...),
    description: str = Form(...),
    files: list[UploadFile] = File(default=[])
):
    try:
        ...
    except ProfileNotFound:
        raise HTTPException(status_code=404, detail="Not found")
```

---

## ❌ Forbidden Practices

| ❌ Do Not                         | ✅ Do Instead                                   |
|----------------------------------|-------------------------------------------------|
| Raise `HTTPException` in service | Raise a domain-specific error                   |
| Log errors without context       | Use `log_exception(e, "while...")`              |
| Write custom `dict` formats      | Use Pydantic models                             |
| Duplicate file/timestamp logic  | Use shared utils                                |
| Catch `Exception` without re-raising | Always raise a `BusinessException`         |

---

## 📌 Summary Checklist

✅ Services:
- [ ] Raise only `BusinessException` subclasses
- [ ] Use `utc_now_iso()` for timestamps
- [ ] Handle all filesystem errors gracefully
- [ ] Return Pydantic models

✅ Controllers:
- [ ] Use `Form(...)` and `File(...)` properly
- [ ] Catch and translate only known business exceptions
- [ ] Log all unexpected errors

✅ Code style:
- [ ] Use structured logging
- [ ] Document all functions
- [ ] Keep business logic out of routes
- [ ] Avoid duplicated logic (timestamps, paths, token count...)

---

## 🆘 Got questions?

Start by reading an existing clean module like `ChatProfileService`. Then ask a senior if you're unsure. **No copy-paste without understanding.**

Let’s build a clean, robust backend together 💪
