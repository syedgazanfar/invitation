# AI Views Refactoring - Usage Guide

## Overview

Two automated scripts are provided to refactor `apps/backend/src/apps/ai/views.py` (1,496 lines) into a modular structure.

## Scripts Available

### 1. `refactor_ai_views_advanced.py` ⭐ **RECOMMENDED**
- Uses Python's AST (Abstract Syntax Tree) for parsing
- Accurately extracts classes and functions
- Preserves comments and docstrings
- Automatically detects imports
- Most reliable and safe

### 2. `refactor_ai_views.py`
- Simple line-range based extraction
- Faster but less accurate
- May require manual fixes
- Backup option if AST script has issues

---

## Quick Start (Recommended Method)

### Step 1: Run the Advanced Script

```bash
# From project root directory
python refactor_ai_views_advanced.py
```

**Expected Output:**
```
==========================================
  Advanced AI Views Refactoring (AST-based)
==========================================

✓ Target: apps/backend/src/apps/ai/views.py

[Step 1] Parsing views.py with AST...
  ✓ Successfully parsed 1496 lines
  ✓ Found class: PhotoAnalysisViewSet → photo_analysis.py
  ✓ Found class: GeneratedMessageViewSet → photo_analysis.py
  ...

[Step 2] Creating backup...
  ✓ Backup created: views_backup.py

[Step 3] Creating views/ directory...
  ✓ Directory ready

[Step 4] Creating module files...
  ✓ Creating helpers.py...
  ✓ Creating photo_analysis.py...
  ✓ Creating message_generation.py...
  ✓ Creating recommendations.py...
  ✓ Creating usage.py...

[Step 5] Creating __init__.py...
  ✓ Created __init__.py

==========================================
  ✅ Refactoring Complete!
==========================================
```

---

## Step 2: Verify the Refactoring

### 2.1 Check File Structure

```bash
ls -la apps/backend/src/apps/ai/views/
```

**Expected files:**
```
__init__.py
helpers.py
photo_analysis.py
message_generation.py
recommendations.py
usage.py
```

### 2.2 Verify Imports

```bash
cd apps/backend
python -c "from src.apps.ai.views import PhotoAnalysisViewSet; print('✓ Import successful')"
```

### 2.3 Run Django Checks

```bash
cd apps/backend
python src/manage.py check
```

**Expected:** `System check identified no issues (0 silenced).`

---

## Step 3: Test Endpoints

### Option A: Using Django Test Server

```bash
cd apps/backend
python src/manage.py runserver
```

Then test endpoints with curl or Postman:

```bash
# Test photo analysis endpoint
curl -X GET http://localhost:8000/api/ai/photo-analyses/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test usage stats
curl -X GET http://localhost:8000/api/ai/usage-stats/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Option B: Run Automated Tests

```bash
cd apps/backend
python src/manage.py test apps.ai
```

---

## Step 4: Clean Up (After Verification)

Once you've verified everything works:

```bash
# Remove the old views.py (backup remains)
cd apps/backend/src/apps/ai
rm views.py

# Optionally, keep backup for a while
# The script already created views_backup.py
```

---

## Troubleshooting

### Issue: Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'apps.ai.views.helpers'
```

**Solution:**
1. Check that `views/__init__.py` exists
2. Verify all module files are created
3. Check Python path configuration

### Issue: Missing Classes

**Symptom:**
```
ImportError: cannot import name 'PhotoAnalysisViewSet'
```

**Solution:**
1. Check `views/__init__.py` exports
2. Verify class exists in module file
3. Run: `grep -r "class PhotoAnalysisViewSet" apps/backend/src/apps/ai/views/`

### Issue: Syntax Errors

**Symptom:**
```
SyntaxError: invalid syntax
```

**Solution:**
1. Check the generated module files for syntax issues
2. The AST script should prevent this, but verify:
   ```bash
   python -m py_compile apps/backend/src/apps/ai/views/*.py
   ```

---

## Rollback Instructions

If something goes wrong, you can easily rollback:

### Full Rollback

```bash
cd apps/backend/src/apps/ai

# Restore original file
cp views_backup.py views.py

# Remove new structure
rm -rf views/

# Verify
python -c "from views import PhotoAnalysisViewSet; print('✓ Rollback successful')"
```

### Partial Fix

If only one module has issues, you can manually edit it:

```bash
# Edit the problematic module
nano apps/backend/src/apps/ai/views/photo_analysis.py

# Or copy specific classes from backup
```

---

## What the Script Does

### 1. Parsing Phase
- Reads `views.py` (1,496 lines)
- Uses Python AST to parse the code
- Identifies all classes and functions
- Maps classes to target modules
- Extracts imports and constants

### 2. Extraction Phase
- Creates `views/` directory
- Generates focused module files:
  - `helpers.py` (140 lines) - Response helpers
  - `photo_analysis.py` (~400 lines) - 4 view classes
  - `message_generation.py` (~450 lines) - 7 view classes
  - `recommendations.py` (~350 lines) - 4 view classes
  - `usage.py` (~250 lines) - 3 view classes

### 3. Integration Phase
- Creates `__init__.py` with all exports
- Preserves all imports and dependencies
- Maintains compatibility with existing code

### 4. Safety Phase
- Creates `views_backup.py` before any changes
- Keeps original `views.py` unchanged initially
- Provides rollback instructions

---

## Module Breakdown

### `helpers.py`
**Functions:**
- `create_success_response()` - Standard success response
- `create_error_response()` - Standard error response
- `add_rate_limit_headers()` - Rate limit headers

**Constants:**
- `MAX_FILE_SIZE_MB`, `MAX_FILE_SIZE_BYTES`
- `ALLOWED_IMAGE_TYPES`
- `RATE_LIMIT_HEADER`, `RATE_LIMIT_REMAINING_HEADER`, `RATE_LIMIT_RESET_HEADER`

### `photo_analysis.py`
**Classes:**
- `PhotoAnalysisViewSet` - CRUD for photo analyses
- `GeneratedMessageViewSet` - CRUD for generated messages
- `PhotoAnalysisView` - Main photo analysis endpoint
- `ColorExtractionView` - Color extraction endpoint

### `message_generation.py`
**Classes:**
- `MoodDetectionView` - Detect mood from photo
- `GenerateMessagesView` - Generate invitation messages
- `GenerateHashtagsView` - Generate hashtags
- `AnalyzePhotoView` - Quick photo analysis
- `ExtractColorsView` - Extract colors
- `DetectMoodView` - Detect mood
- `MessageStylesView` - Available message styles

### `recommendations.py`
**Classes:**
- `StyleRecommendationsView` - Style recommendations
- `TemplateRecommendationsView` - Template recommendations
- `RecommendTemplatesView` - Recommend templates
- `RecommendStylesView` - Recommend styles

### `usage.py`
**Classes:**
- `AIUsageStatsView` - Usage statistics
- `AIUsageLimitsView` - Usage limits
- `SmartSuggestionsView` - Smart suggestions

---

## Benefits After Refactoring

### Before:
- ❌ Single 1,496-line file
- ❌ 18 view classes mixed together
- ❌ Hard to navigate
- ❌ Difficult to maintain
- ❌ Large git diffs

### After:
- ✅ 5 focused modules (140-450 lines each)
- ✅ Logical grouping by functionality
- ✅ Easy to find specific features
- ✅ Clear module responsibilities
- ✅ Smaller, focused git diffs
- ✅ Better testability
- ✅ Easier onboarding

---

## Advanced Usage

### Running with Dry-Run (Preview)

To see what the script will do without making changes:

```python
# Edit refactor_ai_views_advanced.py
# Add at the top of main():
DRY_RUN = True

# Then run:
python refactor_ai_views_advanced.py
```

### Custom Module Mapping

To change which classes go to which modules, edit `CLASS_TO_MODULE` in the script:

```python
CLASS_TO_MODULE = {
    'PhotoAnalysisViewSet': 'your_custom_module',
    # ... other mappings
}
```

### Generating Documentation

After refactoring, generate documentation:

```bash
cd apps/backend
python src/manage.py show_urls | grep ai
```

---

## Post-Refactoring Checklist

- [ ] All module files created
- [ ] `__init__.py` created with exports
- [ ] No import errors (`python manage.py check`)
- [ ] All endpoints accessible
- [ ] Tests pass (`python manage.py test apps.ai`)
- [ ] URLs resolve correctly
- [ ] API documentation updated (if applicable)
- [ ] Old `views.py` removed (after thorough testing)
- [ ] Backup kept for at least 30 days

---

## Support

If you encounter issues:

1. Check the backup: `views_backup.py`
2. Review generated files for syntax errors
3. Verify imports in `__init__.py`
4. Test individual modules:
   ```bash
   python -c "from apps.backend.src.apps.ai.views.photo_analysis import PhotoAnalysisViewSet"
   ```

---

## Timeline

**Estimated time:**
- Script execution: 5-10 seconds
- Verification: 5-10 minutes
- Testing: 15-20 minutes
- **Total: ~30 minutes**

---

**Ready to proceed? Run the script and verify!**

```bash
python refactor_ai_views_advanced.py
```
