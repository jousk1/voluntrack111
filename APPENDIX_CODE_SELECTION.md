# Code Selection for Appendix

This document identifies the specific lines of custom code (non-standard Django) that should be included in your appendix.

## 1. Models (`hub/models.py`)
**Include ALL lines (1-155)** - All models are custom:
- `Department` model (lines 8-16)
- `Profile` model with coordinator logic (lines 19-36)
- `Event` model with capacity methods (lines 39-86)
- `Signup` model (lines 89-106)
- `Contribution` model with approval workflow methods (lines 109-154)

**Key custom methods:**
- `Event.get_confirmed_count()` (lines 69-71)
- `Event.get_remaining_capacity()` (lines 73-77)
- `Event.is_full()` (lines 79-83)
- `Contribution.approve()` (lines 138-143)
- `Contribution.reject()` (lines 145-151)

## 2. Views (`hub/views.py`)
**Include these specific sections:**

### Role-based Dashboard Logic
- Lines 67-129: `dashboard()` function - Shows different dashboards for coordinators vs volunteers

### Event Signup Logic
- Lines 204-217: `event_signup()` - Custom signup validation and capacity checking

### Contribution Creation with Validation
- Lines 252-288: `contribution_create()` - Custom validation for event signups and coordinator permissions

### Reports with Analytics
- Lines 292-351: `reports()` - Custom aggregation queries for top volunteers and department statistics

### Approval Workflow
- Lines 486-517: `approval_approve()` and `approval_reject()` - Custom approval/rejection logic

### Coordinator Management
- Lines 614-662: `coordinator_management()` - Custom user promotion/demotion logic

**Skip these (standard Django patterns):**
- Lines 23-24: Simple render (standard)
- Lines 27-39: Error handlers (standard pattern)
- Lines 42-62: Registration (mostly standard)
- Lines 133-165: `events_list()` (standard filtering/pagination)
- Lines 168-201: `event_detail()` (standard detail view)
- Lines 220-248: Standard list/cancel views
- Lines 356-404: Standard CRUD operations (create/edit/delete)

## 3. Forms (`hub/forms.py`)
**Include ALL lines (1-139)** - All forms have custom logic:
- `UserRegistrationForm` with email/name fields (lines 9-34)
- `ContributionForm` with dynamic queryset filtering based on user role (lines 36-96)
- `EventForm` with department handling (lines 99-138)

**Key custom logic:**
- Lines 49-54: Event queryset filtering for non-coordinators
- Lines 73-74: Department pre-filling based on user profile

## 4. Decorators (`hub/decorators.py`)
**Include ALL lines (1-16)** - Custom access control decorator

## 5. Signals (`hub/signals.py`)
**Include ALL lines (1-15)** - Auto Profile creation on User creation

## 6. Admin (`hub/admin.py`)
**Include ALL lines (1-84)** - Custom admin configuration:
- ProfileInline (lines 12-17)
- UserAdmin extension (lines 20-26)
- All model admin classes (lines 31-83)

## 7. URLs (`hub/urls.py`)
**Include ALL lines (1-45)** - Shows the complete URL structure

## 8. Root URLs (`voluntrack/urls.py`)
**Include lines 12-15** - Custom error handlers (lines 13-15)

## 9. Settings (`voluntrack/settings.py`)
**Include only custom settings:**
- Lines 119-131: Custom project settings section (STATICFILES_DIRS, authentication redirects)

**Skip:** Standard Django settings (lines 1-118)

---

## Summary by File

| File | Lines to Include | Reason |
|------|-----------------|--------|
| `hub/models.py` | **1-155** (ALL) | All custom models |
| `hub/views.py` | **67-129, 204-217, 252-288, 292-351, 486-517, 614-662** | Custom business logic |
| `hub/forms.py` | **1-139** (ALL) | All custom forms |
| `hub/decorators.py` | **1-16** (ALL) | Custom decorator |
| `hub/signals.py` | **1-15** (ALL) | Custom signal |
| `hub/admin.py` | **1-84** (ALL) | Custom admin config |
| `hub/urls.py` | **1-45** (ALL) | URL structure |
| `voluntrack/urls.py` | **12-15** | Error handlers |
| `voluntrack/settings.py` | **119-131** | Custom settings only |

**Total approximate lines: ~600-700 lines of custom code**

