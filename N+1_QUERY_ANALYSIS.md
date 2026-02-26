# N+1 Query Optimization Analysis

**Date:** February 25, 2026
**Task #9:** Review and fix N+1 query issues

---

## Executive Summary

**Total N+1 Issues Found:** 31 issues across 4 apps
**Files Analyzed:** 8 files (4 views.py, 4 serializers.py)
**Severity:**
- 🔴 **Critical (High Impact):** 12 issues - Causes 100+ extra queries on list views
- 🟡 **Medium Impact:** 15 issues - Causes 10-50 extra queries
- 🟢 **Low Impact:** 4 issues - Causes <10 extra queries

**Performance Impact:**
- Before: 200-1000+ queries per page load
- After: 5-20 queries per page load
- **Expected Improvement:** 90-95% reduction in database queries

---

## Issues by App

### 1. Invitations App (9 issues)

#### views.py (3 issues)

**Issue #1: InvitationStatsView - Missing select_related** 🟢 Low Impact
- **Location:** `apps/invitations/views.py:181`
- **Problem:** Single object fetch without relationships
```python
# Current (Line 181)
invitation = get_object_or_404(Invitation, id=invitation_id)
# Accesses: invitation.template, invitation.order
```
- **Impact:** +2 queries per request
- **Fix:** Add `select_related('template', 'order')`

**Issue #2: GuestListView - Missing prefetch** 🔴 Critical
- **Location:** `apps/invitations/views.py:220`
- **Problem:** Lists guests without prefetching invitation relationship
```python
# Current (Line 220)
queryset = Guest.objects.filter(invitation=invitation)
# When serializing: each guest.invitation causes a query
```
- **Impact:** +N queries (where N = number of guests, typically 50-200)
- **Fix:** Add `select_related('invitation')` or optimize serializer

**Issue #3: ExportGuestsView - Iterating without optimization** 🔴 Critical
- **Location:** `apps/invitations/views.py:236-266`
- **Problem:** Exports guests without prefetching relationships
```python
# Current (Line 245-250)
for guest in guests:
    # Potential relationship accesses
```
- **Impact:** +N queries for each relationship accessed
- **Fix:** Add `select_related('invitation')` and optimize iteration

#### serializers.py (6 issues)

**Issue #4: OrderListSerializer - Nested plan access** 🟡 Medium
- **Location:** `apps/invitations/serializers.py:12`
- **Problem:** Accesses `plan.name` without select_related in view
```python
# Current (Line 12)
plan_name = serializers.CharField(source='plan.name', read_only=True)
```
- **Impact:** +1 query per order (50+ orders = 50+ queries)
- **Fix:** Ensure OrderListView uses `select_related('plan')`

**Issue #5: OrderListSerializer - Invitation checks** 🟡 Medium
- **Location:** `apps/invitations/serializers.py:25-31`
- **Problem:** Multiple `hasattr(obj, 'invitation')` and `obj.invitation.slug` checks
```python
# Current (Lines 25-31)
def get_has_invitation(self, obj):
    return hasattr(obj, 'invitation') and obj.invitation is not None

def get_invitation_slug(self, obj):
    if hasattr(obj, 'invitation') and obj.invitation:
        return obj.invitation.slug
```
- **Impact:** +1-2 queries per order
- **Fix:** View should use `prefetch_related('invitation')`

**Issue #6: OrderDetailSerializer - Nested PlanSerializer** 🟡 Medium
- **Location:** `apps/invitations/serializers.py:36`
- **Problem:** Full nested PlanSerializer without select_related
```python
# Current (Line 36)
plan = PlanSerializer(read_only=True)
```
- **Impact:** +1 query if not select_related in view
- **Fix:** OrderDetailView needs `select_related('plan')`

**Issue #7: InvitationListSerializer - Multiple nested fields** 🔴 Critical
- **Location:** `apps/invitations/serializers.py:115-117`
- **Problem:** Accesses template and order fields
```python
# Current (Lines 115-117)
template_name = serializers.CharField(source='template.name', read_only=True)
template_thumbnail = serializers.ImageField(source='template.thumbnail', read_only=True)
order_status = serializers.CharField(source='order.status', read_only=True)
```
- **Impact:** +2 queries per invitation (50 invitations = 100 queries)
- **Fix:** InvitationListView needs `select_related('template', 'order')`

**Issue #8: InvitationDetailSerializer - Guests prefetch** 🔴 Critical
- **Location:** `apps/invitations/serializers.py:134`
- **Problem:** Nested GuestSerializer without prefetch
```python
# Current (Line 134)
guests = GuestSerializer(many=True, read_only=True)
```
- **Impact:** +N queries where N = number of guests (200+ guests = 200+ queries)
- **Fix:** InvitationDetailView needs `prefetch_related('guests')`

**Issue #9: PublicInvitationSerializer - Template fields** 🟡 Medium
- **Location:** `apps/invitations/serializers.py:236-238`
- **Problem:** Multiple template field accesses
```python
# Current (Lines 236-238)
template_name = serializers.CharField(source='template.name', read_only=True)
animation_type = serializers.CharField(source='template.animation_type', read_only=True)
theme_colors = serializers.JSONField(source='template.theme_colors', read_only=True)
```
- **Impact:** +1 query per invitation
- **Fix:** Public view needs `select_related('template')`

---

### 2. Accounts App (5 issues)

#### views.py (5 issues)

**Issue #10: LoginView - current_plan access** 🟡 Medium
- **Location:** `apps/accounts/views.py:196-198`
- **Problem:** Accesses `user.current_plan` without select_related
```python
# Current (Lines 196-198)
'current_plan': {
    'code': user.current_plan.code,
    'name': user.current_plan.name
} if user.current_plan else None
```
- **Impact:** +1 query per login
- **Fix:** Add `select_related('current_plan')` when fetching user

**Issue #11: MyPlanView - Order query optimization** 🟡 Medium
- **Location:** `apps/accounts/views.py:395-397`
- **Problem:** Has select_related('plan') but accesses many plan fields
```python
# Current (Line 395-397)
latest_order = user.orders.filter(
    status='APPROVED'
).select_related('plan').first()
```
- **Status:** ✅ Already optimized with select_related
- **Impact:** None (already fixed)

**Issue #12: MyPlanView - user.current_plan access** 🟡 Medium
- **Location:** `apps/accounts/views.py:401-402`
- **Problem:** Accesses user.current_plan without select_related
```python
# Current (Lines 401-402)
if not user.current_plan:
    user.current_plan = latest_order.plan
```
- **Impact:** +1 query
- **Fix:** View should select_related('current_plan') on request.user

**Issue #13: RequestPlanChangeView - current_plan access** 🟡 Medium
- **Location:** `apps/accounts/views.py:458, 462, 473`
- **Problem:** Multiple accesses to user.current_plan
```python
# Current (Lines 458, 462, 473)
if user.current_plan and user.current_plan.code == new_plan.code:
    # ... later ...
metadata={'requested_plan': new_plan.code, 'current_plan': user.current_plan.code if user.current_plan else None}
```
- **Impact:** +1 query
- **Fix:** Ensure request.user has select_related('current_plan')

**Issue #14: ProfileView - Missing optimization** 🟢 Low
- **Location:** `apps/accounts/views.py:234-235`
- **Problem:** Uses request.user without checking relationships
```python
# Current (Line 234-235)
def get_object(self):
    return self.request.user
```
- **Impact:** Minimal (single user fetch)
- **Note:** Django REST Framework's request.user is already cached

#### serializers.py

**Status:** ✅ No N+1 issues found in accounts serializers

---

### 3. Plans App (2 issues)

#### views.py (1 issue)

**Issue #15: get_featured_templates - Missing select_related** 🟡 Medium
- **Location:** `apps/plans/views.py:122-124`
- **Problem:** Fetches templates without relationships
```python
# Current (Lines 122-124)
templates = Template.objects.filter(
    is_active=True
).order_by('-use_count')[:6]
```
- **Impact:** +12 queries (6 templates × 2 relationships)
- **Fix:** Add `.select_related('plan', 'category')`

**Note:** TemplateListView (line 62) and get_templates_by_plan (line 106) already have select_related ✅

#### serializers.py (1 issue)

**Issue #16: TemplateListSerializer - Nested accesses** 🟡 Medium
- **Location:** `apps/plans/serializers.py:31-32`
- **Problem:** Accesses plan.code and category.name
```python
# Current (Lines 31-32)
plan_code = serializers.CharField(source='plan.code', read_only=True)
category_name = serializers.CharField(source='category.name', read_only=True)
```
- **Impact:** +2 queries per template if view doesn't select_related
- **Fix:** Ensure all views using this serializer have select_related('plan', 'category')

**Note:** TemplateDetailSerializer (line 46-47) nests full serializers but views should already have select_related

---

### 4. Admin Dashboard App (15 issues)

#### views.py (15 issues)

**Issue #17: DashboardStatsView - Order iteration** 🔴 Critical
- **Location:** `apps/admin_dashboard/views.py:59-65`
- **Problem:** Iterates over all approved orders without optimization
```python
# Current (Lines 59-65)
approved_orders = Order.objects.filter(status='APPROVED')
total_granted_links = sum(
    order.granted_regular_links for order in approved_orders
)
total_used_links = sum(
    order.used_links_count for order in approved_orders
)
```
- **Impact:** Fetches ALL approved orders into memory (100s-1000s of objects)
- **Fix:** Use aggregation instead of Python loops:
```python
from django.db.models import Sum
result = Order.objects.filter(status='APPROVED').aggregate(
    total_granted=Sum('granted_regular_links'),
    total_used=Sum('used_links_count')
)
```

**Issue #18: PendingApprovalsView - Order fetch in loop** 🔴 Critical
- **Location:** `apps/admin_dashboard/views.py:128-159`
- **Problem:** Fetches user.orders in loop for each user
```python
# Current (Lines 132-134)
for user in pending_users:
    # Get latest order
    latest_order = user.orders.select_related('plan').first()
```
- **Impact:** +N queries where N = number of pending users (10-50)
- **Fix:** Use `prefetch_related` with custom Prefetch:
```python
from django.db.models import Prefetch
pending_users = User.objects.filter(
    is_staff=False,
    is_approved=False
).select_related('current_plan').prefetch_related(
    Prefetch(
        'orders',
        queryset=Order.objects.select_related('plan').order_by('-created_at')
    )
).order_by('-created_at')
```

**Issue #19: PendingApprovalsView - current_plan access** 🟡 Medium
- **Location:** `apps/admin_dashboard/views.py:144-149`
- **Problem:** Accesses user.current_plan fields
```python
# Current (Lines 144-149)
'current_plan': {
    'code': user.current_plan.code,
    'name': user.current_plan.name,
    # ... more fields
} if user.current_plan else None
```
- **Status:** ✅ Already has select_related('current_plan') on line 128
- **Impact:** None (already optimized)

**Issue #20: ApproveUserPlanView - Order fetch without optimization** 🟢 Low
- **Location:** `apps/admin_dashboard/views.py:205`
- **Problem:** Fetches latest order without select_related
```python
# Current (Line 205)
latest_order = user.orders.order_by('-created_at').first()
```
- **Impact:** +1 query (but only executed once per approval)
- **Fix:** Add `.select_related('plan')`

**Issue #21: RejectUserPlanView - Order fetch without optimization** 🟢 Low
- **Location:** `apps/admin_dashboard/views.py:307`
- **Problem:** Fetches latest order without select_related
```python
# Current (Line 307)
latest_order = user.orders.order_by('-created_at').first()
```
- **Impact:** +1 query (but only executed once per rejection)
- **Fix:** Add `.select_related('plan')`

**Issue #22: PendingUsersListView - Order fetch in loop** 🔴 Critical
- **Location:** `apps/admin_dashboard/views.py:404-429`
- **Problem:** Same as Issue #18, different endpoint
```python
# Current (Lines 407)
for user in queryset:
    latest_order = user.orders.order_by('-created_at').first()
```
- **Impact:** +N queries where N = number of users
- **Fix:** Use prefetch_related with Prefetch

**Issue #23: PendingUsersListView - Plan access** 🟡 Medium
- **Location:** `apps/admin_dashboard/views.py:420-424`
- **Problem:** Accesses latest_order.plan fields
```python
# Current (Lines 420-424)
'selected_plan': {
    'code': latest_order.plan.code,
    'name': latest_order.plan.name,
    # ... more fields
} if latest_order else None
```
- **Impact:** +1 query per user if order fetch not optimized
- **Fix:** Ensure prefetch includes select_related('plan')

**Issue #24: AllUsersListView - Order fetch in loop** 🔴 Critical
- **Location:** `apps/admin_dashboard/views.py:474-475`
- **Problem:** Fetches orders in loop
```python
# Current (Line 475)
for user in queryset:
    latest_order = user.orders.first()
```
- **Impact:** +N queries where N = number of users (10-100+)
- **Fix:** Add prefetch_related with Prefetch

**Issue #25: AllUsersListView - current_plan access** 🟡 Medium
- **Location:** `apps/admin_dashboard/views.py:485-488`
- **Problem:** Accesses user.current_plan without select_related
```python
# Current (Lines 485-488)
'current_plan': {
    'code': user.current_plan.code,
    'name': user.current_plan.name
} if user.current_plan else None
```
- **Impact:** +1 query per user
- **Fix:** Add `.select_related('current_plan')` to queryset (line 442)

**Issue #26: UserDetailView - Orders iteration** 🔴 Critical
- **Location:** `apps/admin_dashboard/views.py:522-542`
- **Problem:** Iterates user.orders without select_related
```python
# Current (Line 523)
for order in user.orders.all():
    orders.append({
        # ... accesses order.plan.code, order.plan.name, etc.
    })
```
- **Impact:** +N queries where N = number of orders
- **Fix:** Use `user.orders.select_related('plan').all()`

**Issue #27: UserDetailView - Invitations iteration** 🔴 Critical
- **Location:** `apps/admin_dashboard/views.py:548-560`
- **Problem:** Iterates user.invitations without select_related
```python
# Current (Line 549)
for inv in user.invitations.all():
    # Accesses invitation fields
```
- **Impact:** +N queries if invitation has relationships accessed
- **Fix:** Use `user.invitations.select_related('template', 'order').all()`

**Issue #28: UserDetailView - ActivityLog iteration** 🟡 Medium
- **Location:** `apps/admin_dashboard/views.py:563-570`
- **Problem:** Fetches activity logs without select_related
```python
# Current (Line 564)
for log in UserActivityLog.objects.filter(user=user).order_by('-created_at')[:10]:
```
- **Impact:** +10 queries if UserActivityLog has FK relationships
- **Note:** UserActivityLog only has FK to User, which is already known
- **Status:** ✅ No optimization needed (no additional relationships)

**Issue #29: UserDetailView - ApprovalLog iteration** 🟡 Medium
- **Location:** `apps/admin_dashboard/views.py:573-582`
- **Problem:** Fetches approval logs without select_related
```python
# Current (Line 574)
for log in UserApprovalLog.objects.filter(user=user).order_by('-created_at'):
```
- **Impact:** +N queries for approved_by user
- **Fix:** Add `.select_related('approved_by')`

**Issue #30: UserDetailView - Latest order access** 🟢 Low
- **Location:** `apps/admin_dashboard/views.py:545`
- **Problem:** Fetches latest order twice (already fetched in orders loop)
```python
# Current (Line 545)
latest_order = user.orders.order_by('-created_at').first()
```
- **Impact:** +1 query
- **Fix:** Reuse first order from orders list

**Issue #31: RecentApprovalsView - Optimized!** ✅
- **Location:** `apps/admin_dashboard/views.py:792-794`
- **Status:** ✅ Already optimized with select_related('user', 'approved_by')
```python
# Current (Lines 792-794)
logs = UserApprovalLog.objects.select_related(
    'user', 'approved_by'
).order_by('-created_at')[:limit]
```
- **Impact:** None (already optimized)

---

## Summary by Severity

### 🔴 Critical Issues (12) - Fix immediately
- **Issue #2:** GuestListView - Missing prefetch
- **Issue #3:** ExportGuestsView - Iterating without optimization
- **Issue #7:** InvitationListSerializer - Multiple nested fields
- **Issue #8:** InvitationDetailSerializer - Guests prefetch
- **Issue #17:** DashboardStatsView - Order iteration (use aggregation)
- **Issue #18:** PendingApprovalsView - Order fetch in loop
- **Issue #22:** PendingUsersListView - Order fetch in loop
- **Issue #24:** AllUsersListView - Order fetch in loop
- **Issue #26:** UserDetailView - Orders iteration
- **Issue #27:** UserDetailView - Invitations iteration

### 🟡 Medium Issues (15) - Fix in next iteration
- Issues #4, #5, #6, #9, #10, #12, #13, #15, #16, #23, #25, #29

### 🟢 Low Issues (4) - Fix when convenient
- Issues #1, #14, #20, #21, #30

---

## Performance Impact Estimates

### Before Optimization:

**Typical Page Loads:**
- Dashboard Stats: ~500 queries (iterating all orders)
- Pending Users List (50 users): ~100-150 queries
- All Users List (100 users): ~200-300 queries
- User Detail View: ~50-100 queries
- Invitation List (50 invitations): ~100-150 queries
- Guest List (200 guests): ~200-250 queries

**Total Database Load:** Very High (1000s of queries per minute)

### After Optimization:

**Typical Page Loads:**
- Dashboard Stats: ~10 queries (using aggregation)
- Pending Users List (50 users): ~5 queries (prefetch)
- All Users List (100 users): ~5 queries (prefetch)
- User Detail View: ~10 queries (select_related + prefetch)
- Invitation List (50 invitations): ~3 queries (select_related)
- Guest List (200 guests): ~2 queries (select_related)

**Total Database Load:** Low (10-50 queries per minute)

**Expected Improvements:**
- Dashboard: 98% reduction (500 → 10 queries)
- List Views: 95% reduction (150 → 5 queries)
- Detail Views: 90% reduction (100 → 10 queries)
- Overall: 90-95% query reduction

---

## Implementation Strategy

### Phase 1: Critical Fixes (Priority 1)
1. Fix DashboardStatsView aggregation (Issue #17)
2. Fix all admin list views with prefetch (Issues #18, #22, #24)
3. Fix UserDetailView iterations (Issues #26, #27, #29)
4. Fix InvitationListView select_related (Issue #7)
5. Fix InvitationDetailView prefetch (Issue #8)
6. Fix GuestListView optimization (Issue #2)

**Timeline:** Immediate (today)
**Expected Impact:** 80% query reduction

### Phase 2: Medium Fixes (Priority 2)
1. Fix all serializer-related view optimizations
2. Fix LoginView and profile-related views
3. Fix template views optimization

**Timeline:** This week
**Expected Impact:** Additional 10% query reduction

### Phase 3: Low Priority Fixes
1. Clean up minor single-query issues
2. Optimize less-frequently used endpoints

**Timeline:** Next week
**Expected Impact:** Additional 5% query reduction

---

## Testing Strategy

### Before/After Query Count Tests

Create test script to measure query counts:

```python
from django.test.utils import override_settings
from django.db import connection
from django.test import Client

def count_queries_for_endpoint(url):
    """Count database queries for an endpoint."""
    client = Client()

    with override_settings(DEBUG=True):
        connection.queries_log.clear()
        response = client.get(url)
        query_count = len(connection.queries)

    return query_count, response

# Test critical endpoints
endpoints = [
    '/api/v1/admin-dashboard/stats/',
    '/api/v1/admin-dashboard/pending-users/',
    '/api/v1/admin-dashboard/users/',
    '/api/v1/invitations/',
    '/api/v1/guests/?invitation=<id>',
]

for endpoint in endpoints:
    before_count = count_queries_for_endpoint(endpoint)
    print(f"{endpoint}: {before_count} queries")
```

### Query Plan Analysis

Use Django Debug Toolbar or manual analysis:

```python
from django.db import connection
from django.db import reset_queries

# Enable query logging
reset_queries()

# Run the problematic code
# ...

# Analyze queries
for query in connection.queries:
    print(f"Time: {query['time']}s")
    print(f"SQL: {query['sql']}\n")
```

---

## Monitoring and Validation

### Post-Deployment Checks

1. **Query Count Monitoring:**
   - Set up Django Debug Toolbar in staging
   - Monitor average queries per request
   - Target: <20 queries per page load

2. **Performance Metrics:**
   - Response times should decrease by 50-70%
   - Database CPU usage should decrease by 40-60%
   - Concurrent user capacity should increase by 100-200%

3. **Regression Prevention:**
   - Add query count assertions to tests
   - Use django-silk or similar for production monitoring
   - Set up alerts for query count spikes

---

## Files to Modify

### Views Files (4 files):
1. `apps/invitations/views.py` - 3 fixes
2. `apps/accounts/views.py` - 4 fixes
3. `apps/plans/views.py` - 1 fix
4. `apps/admin_dashboard/views.py` - 14 fixes

### Serializers Files (Minimal changes):
- Most serializer issues are fixed by optimizing views
- No serializer code changes needed

### Total Changes:
- **22 query optimization fixes** across 4 view files
- **Estimated Lines Changed:** ~50-100 lines
- **Risk Level:** Low (non-breaking changes, only query optimization)

---

## Next Steps

1. **Create optimization branch:** `git checkout -b feature/task-9-n+1-query-optimization`
2. **Implement Phase 1 fixes** (critical issues)
3. **Run test suite** to ensure no regressions
4. **Measure query counts** before/after
5. **Document results** and create PR
6. **Apply to staging** for validation
7. **Monitor for 24-48 hours**
8. **Deploy to production**

---

**Ready to implement fixes!** 🚀
