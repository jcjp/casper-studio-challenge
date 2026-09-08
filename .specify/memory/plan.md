# Implementation Plan: Recipe Enhancement Pipeline Fix

**Branch**: `fix/multi-modification-parsing` | **Date**: 2026-09-08 | **Spec**: `.specify/memory/spec.md`

## Summary

Fix the recipe enhancement pipeline to correctly extract and apply ALL discrete modifications from review text. The core issue is that `extract_single_modification()` processes only ONE random review and the prompt/schema forces modifications into a single category. Solution: modify the prompt to return an array of modifications, update the extraction flow to process all reviews, and verify against all 6 sample recipes.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: OpenAI (gpt-3.5-turbo), Pydantic, Loguru, python-dotenv

**Storage**: JSON files (data/*.json -> data/enhanced/*.json)

**Testing**: Manual pipeline runs via `src/test_pipeline.py`

**Target Platform**: CLI / Local execution

**Project Type**: LLM pipeline / data processing

**Performance Goals**: Process all 6 recipes without errors

**Constraints**: 4-hour time limit; must work with existing OpenAI API key

**Scale/Scope**: 6 sample recipes, ~20 total reviews with modifications

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Correctness Over Speed | VIOLATED | Current code extracts partial modifications |
| II. Transparency & Attribution | PASS | Schema supports full attribution |
| III. Robustness at Scale | VIOLATED | Only 2/6 recipes produce output |
| IV. Test-Driven Validation | VIOLATED | No automated tests; manual verification only |
| V. Incremental Progress | PASS | Plan prioritizes high-impact fixes |

## Project Structure

### Existing Source Code

```text
src/
├── llm_pipeline/
│   ├── __init__.py
│   ├── enhanced_recipe_generator.py  # Step 3: Generate enhanced output
│   ├── models.py                      # Pydantic models (ModificationObject, etc.)
│   ├── pipeline.py                    # Main orchestrator - NEEDS CHANGES
│   ├── prompts.py                     # LLM prompts - NEEDS CHANGES
│   ├── recipe_modifier.py             # Step 2: Apply edits
│   └── tweak_extractor.py             # Step 1: Extract mods - NEEDS CHANGES
├── scraper_v2.py                      # Recipe scraper (not in scope)
└── test_pipeline.py                   # Test runner

data/
├── recipe_*.json                      # 6 input recipes
└── enhanced/                          # Output directory
```

### Files to Modify (Priority Order)

1. **`prompts.py`** - Update prompt to request array of modifications, not single object
2. **`models.py`** - Add `ModificationList` model to handle array response
3. **`tweak_extractor.py`** - Change `extract_modification()` to return list; rename `extract_single_modification()` to `extract_all_modifications()` to process all reviews
4. **`pipeline.py`** - Update `process_single_recipe()` to handle multiple modifications from multiple reviews
5. **`enhanced_recipe_generator.py`** - Already supports multiple modifications; may need minor updates

## Implementation Phases

### Phase 1: Prompt & Schema Fix (Est. 1 hour)

**Goal**: LLM returns ALL modifications from a single review

Changes:
1. Update `prompts.py:build_simple_prompt()` to request array of modifications
2. Add new model `ModificationList` in `models.py` containing `List[ModificationObject]`
3. Update `tweak_extractor.py:extract_modification()` to parse array response

**Verification**: Manually test with the "4 tweaks" chocolate chip review, confirm 4 modifications returned.

### Phase 2: Multi-Review Processing (Est. 1 hour)

**Goal**: Process ALL reviews for a recipe, not just one random one

Changes:
1. Rename `extract_single_modification()` to `extract_all_modifications()`
2. Loop through all `has_modification` reviews
3. Aggregate all modifications into single list
4. Update `pipeline.py:process_single_recipe()` to call new method

**Verification**: Run on chocolate chip recipe, confirm modifications from all 4 reviews captured.

### Phase 3: Recipe Modifier Updates (Est. 30 min)

**Goal**: Apply multiple modifications sequentially

Changes:
1. Use existing `apply_modifications_batch()` method (already exists!)
2. Handle conflicts: later modifications win, or warn on overlap
3. Improve logging to show all applied changes

**Verification**: Enhanced output shows all changes with correct attribution.

### Phase 4: Full Pipeline Test & Documentation (Est. 1.5 hours)

**Goal**: All 6 recipes processed; comprehensive analysis doc written

Changes:
1. Run `test_pipeline.py all`
2. Fix any edge case failures
3. Write `ANALYSIS.md` documenting:
   - Problems found
   - Solutions implemented
   - Technical decisions
   - Future improvements
4. Commit and prepare for submission

**Verification**: 4+ recipes produce valid enhanced output; doc covers all deliverables.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM returns malformed array | Add robust JSON parsing with fallback to wrap single object in array |
| Conflicting modifications break recipe | Apply in order; log conflicts; don't fail on partial success |
| Time runs out | Phase 1 alone delivers value; prioritize working code over perfect code |
| API rate limits | Use existing `max_retries` logic; consider caching LLM responses |

## Success Metrics

- [ ] Chocolate chip cookie review extracts 4 modifications (not 2)
- [ ] All 4 recipes with modifications produce enhanced output
- [ ] Pipeline completes without errors on all 6 recipes
- [ ] `ANALYSIS.md` documents findings and approach
- [ ] Code committed with clear commit messages
