# Plans App Service Layer Blueprint

## Overview

**Current State:** 130-line views.py with basic business logic
**Goal:** Extract business logic into focused service modules

---

## Current Files Analysis

```
views.py - 130 lines
├── PlanListView - List active plans
├── PlanDetailView - Get plan by code
├── CategoryListView - List invitation categories
├── TemplateListView - List templates with filtering
├── TemplateDetailView - Get template details
├── get_templates_by_plan() - Templates by plan hierarchy
└── get_featured_templates() - Popular templates

models.py - 177 lines
├── Plan - Pricing plans (BASIC, PREMIUM, LUXURY)
├── InvitationCategory - Event categories (Wedding, Birthday, etc.)
└── Template - Templates with animations
```

---

## Service Architecture

```
apps/backend/src/apps/plans/services/
├── __init__.py              # Export all services
├── plan_service.py          # Plan management
├── template_service.py      # Template management
├── category_service.py      # Category management
└── recommendation_service.py # Template recommendations
```

---

## Service Modules

### 1. `plan_service.py` - Plan Management

**Purpose:** Handle plan retrieval and hierarchy logic

**Class:** `PlanService`

**Methods:**
- `get_all_active_plans()` - List all active plans
- `get_plan_by_code(plan_code)` - Get plan by code
- `get_plan_by_id(plan_id)` - Get plan by UUID
- `get_plan_hierarchy()` - Get plan tier hierarchy
- `can_access_plan(user_plan_code, target_plan_code)` - Check plan access
- `get_accessible_plans(user_plan_code)` - Get plans user can access
- `compare_plans()` - Get comparison data for all plans

**Business Logic:**
- **Plan Hierarchy:** BASIC (1) < PREMIUM (2) < LUXURY (3)
- **Access Control:** Users can access their tier and below
- **Pricing:** Currently INR only (future: multi-currency)

**Size:** ~150 lines

---

### 2. `template_service.py` - Template Management

**Purpose:** Handle template retrieval, filtering, and usage tracking

**Class:** `TemplateService`

**Methods:**
- `get_all_templates(filters)` - List templates with filtering
- `get_template_by_id(template_id)` - Get template by UUID
- `get_templates_by_plan(plan_code, category)` - Templates by plan hierarchy
- `get_templates_by_category(category_code, plan)` - Templates by category
- `get_featured_templates(limit)` - Popular templates
- `increment_template_usage(template_id)` - Track usage
- `can_user_access_template(user, template)` - Check template access
- `search_templates(query, filters)` - Search templates

**Business Logic:**
- **Plan Hierarchy Access:**
  - BASIC users: Only BASIC templates
  - PREMIUM users: BASIC + PREMIUM templates
  - LUXURY users: All templates
- **Filtering:** By plan, category, animation type, premium status
- **Usage Tracking:** Increment use_count when template is used
- **Ordering:** By popularity (use_count), recency, name

**Size:** ~200 lines

---

### 3. `category_service.py` - Category Management

**Purpose:** Handle invitation categories

**Class:** `CategoryService`

**Methods:**
- `get_all_categories()` - List all active categories
- `get_category_by_code(code)` - Get category by code
- `get_templates_count_by_category()` - Count templates per category
- `get_popular_categories(limit)` - Most used categories

**Business Logic:**
- **Sorting:** By sort_order, then name
- **Template Count:** Get count of active templates per category

**Size:** ~100 lines

---

### 4. `recommendation_service.py` - Template Recommendations

**Purpose:** Provide intelligent template recommendations

**Class:** `RecommendationService`

**Methods:**
- `get_recommended_templates(user, category, limit)` - Personalized recommendations
- `get_similar_templates(template_id, limit)` - Similar templates
- `get_trending_templates(days, limit)` - Trending templates
- `get_templates_for_event(event_type, user_plan)` - Event-specific templates

**Business Logic:**
- **Recommendation Factors:**
  - User's plan tier
  - Category preference
  - Template popularity
  - Recent templates
- **Similar Templates:** By animation type, theme colors, category
- **Trending:** Based on recent usage increase

**Size:** ~150 lines

---

## Benefits

### Before Service Layer:
- ❌ 130 lines with mixed concerns
- ❌ Plan hierarchy logic in views
- ❌ Template filtering logic exposed
- ❌ No recommendation system
- ❌ Hard to add features

### After Service Layer:
- ✅ ~600 lines of organized code
- ✅ Clear separation of concerns
- ✅ Reusable business logic
- ✅ Easy to add recommendations
- ✅ Testable components
- ✅ Ready for future features (caching, analytics)

---

## Key Business Logic

### Plan Hierarchy Logic:
```python
PLAN_HIERARCHY = {
    'BASIC': 1,
    'PREMIUM': 2,
    'LUXURY': 3
}

def can_access_plan(user_plan_code, target_plan_code):
    """
    Users can access their tier and below.

    BASIC user: Only BASIC
    PREMIUM user: BASIC + PREMIUM
    LUXURY user: All
    """
    user_tier = PLAN_HIERARCHY.get(user_plan_code, 0)
    target_tier = PLAN_HIERARCHY.get(target_plan_code, 0)
    return target_tier <= user_tier
```

### Template Access Logic:
```python
def get_accessible_templates(plan_code):
    """
    Get templates user can access based on plan.
    """
    accessible_plans = []

    if plan_code == 'LUXURY':
        accessible_plans = ['BASIC', 'PREMIUM', 'LUXURY']
    elif plan_code == 'PREMIUM':
        accessible_plans = ['BASIC', 'PREMIUM']
    else:  # BASIC
        accessible_plans = ['BASIC']

    return Template.objects.filter(
        plan__code__in=accessible_plans,
        is_active=True
    )
```

---

## Migration Strategy

### Phase 1: Create Services
1. Create `services/` directory
2. Implement `plan_service.py`
3. Implement `template_service.py`
4. Implement `category_service.py`
5. Implement `recommendation_service.py`
6. Create `__init__.py` with exports

### Phase 2: Test Services (Optional)
1. Write unit tests for each service
2. Test plan hierarchy logic
3. Test template filtering
4. Test recommendations

### Phase 3: Refactor Views (Optional)
1. Update views to use services
2. Maintain backward compatibility
3. Test all endpoints

---

## Expected Metrics

### Views Files:
- Before: 130 lines
- After: ~80 lines (38% reduction)

### Services:
- `plan_service.py`: ~150 lines
- `template_service.py`: ~200 lines
- `category_service.py`: ~100 lines
- `recommendation_service.py`: ~150 lines
- `__init__.py`: ~30 lines
- **Total:** ~630 lines (well-organized, testable)

---

## Service Design Principles

1. **Stateless:** No instance state between calls
2. **Caching-Ready:** Easy to add caching layer
3. **Type Hints:** All parameters and returns typed
4. **Error Handling:** Graceful error handling
5. **Logging:** Important operations logged
6. **Testable:** Easy to mock and unit test

---

## Future Enhancements

### Caching:
```python
@cache_decorator(timeout=3600)
def get_all_active_plans():
    """Cache plans for 1 hour"""
    return Plan.objects.filter(is_active=True)
```

### Analytics:
- Track which templates are viewed most
- A/B testing for template recommendations
- User preference learning

### Multi-Currency:
```python
def get_plan_price(plan, currency='INR', country='IN'):
    """Get price in user's currency"""
    if currency == 'INR':
        return plan.price_inr
    elif currency == 'USD':
        return plan.price_usd
    # ... more currencies
```

---

## Integration Points

### With Other Apps:
- **accounts app:** User plan access (from AccountsService)
- **invitations app:** Template selection validation
- **admin_dashboard app:** Plan statistics

### External Services:
- **Redis:** Caching for frequently accessed data
- **Analytics:** Track template usage trends

---

## Testing Strategy

### Unit Tests:
- Plan hierarchy validation
- Template filtering by plan
- Category listing
- Recommendation logic

### Test Coverage Goals:
- Services: 90%+
- Business logic: 100%

---

## Next Steps

1. ✅ Create blueprint document
2. ⏳ Create `services/` directory
3. ⏳ Implement `plan_service.py`
4. ⏳ Implement `template_service.py`
5. ⏳ Implement `category_service.py`
6. ⏳ Implement `recommendation_service.py`
7. ⏳ Implement `__init__.py`
8. ⏳ (Optional) Refactor views
9. ⏳ (Optional) Write unit tests

---

## Summary

The plans app service layer will be the smallest but most reusable:
- Clean plan hierarchy logic
- Flexible template filtering
- Recommendation system foundation
- Ready for caching and optimization
- Easy to extend with new features
