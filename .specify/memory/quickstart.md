# Quickstart Validation Guide

**Feature**: Recipe Enhancement Pipeline Fix  
**Branch**: `fix/multi-modification-parsing`  
**Date**: 2026-09-08

## Prerequisites

- Python 3.13+
- OpenAI API key set: `export OPENAI_API_KEY=sk-...`
- Dependencies installed

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Verify environment
python -c "import openai; print('OpenAI ready')"
```

## Validation Scenarios

### Scenario 1: Multi-Modification Extraction (P1)

**Goal**: Verify LLM extracts ALL modifications from a single review.

**Test Review** (chocolate chip cookies):
> "(1) I used a half cup of sugar and one-and-a-half cups of brown sugar; (2) I omitted the water; (3) I added a teaspoon of cream of tartar to the batter; (4) I refrigerated the batter for at least an hour"

**Run**:
```bash
python src/test_pipeline.py single 10813
```

**Expected**:
- 4 modifications extracted (not 2)
- Types: quantity_adjustment, removal, addition, technique_change
- All logged with source attribution

**Verify**:
```bash
cat data/enhanced/enhanced_10813.json | jq '.modifications_applied | length'
# Expected: >= 4
```

---

### Scenario 2: All Reviews Processed (P2)

**Goal**: Process ALL reviews with modifications, not just one.

**Run**:
```bash
python src/test_pipeline.py single 10813
```

**Expected**:
- All 4 reviews with `has_modification: true` analyzed
- Modifications aggregated from multiple reviews

**Verify**:
```bash
cat data/enhanced/enhanced_10813.json | jq '[.modifications_applied[].source_review.text] | unique | length'
# Expected: 4 (unique reviews)
```

---

### Scenario 3: Full Pipeline Run (P3)

**Goal**: All 6 recipes processed without errors.

**Run**:
```bash
python src/test_pipeline.py all
```

**Expected**:
- 4+ recipes produce enhanced output
- Recipes with 0 modifications log warning, return gracefully
- No unhandled exceptions

**Verify**:
```bash
ls data/enhanced/*.json | wc -l
# Expected: >= 4
```

---

### Scenario 4: Conflict Resolution

**Goal**: Highest-rated review wins on conflicting modifications.

**Setup**: Manually verify a recipe has conflicting modifications across reviews.

**Expected**:
- Modifications applied in rating order (descending)
- Conflict logged with both review sources
- Final ingredient reflects highest-rated review's change

---

### Scenario 5: Edge Cases

| Case | Input | Expected Behavior |
|------|-------|-------------------|
| No reviews | Recipe with empty reviews array | Log warning, skip, no crash |
| No modifications | Reviews without `has_modification` | Skip extraction, no crash |
| LLM returns empty | Review with vague text | Empty modifications array, logged |
| Fuzzy match fail | Ingredient typo in review | Log low confidence, skip application |

---

## Success Criteria Checklist

- [ ] **SC-001**: Chocolate chip review extracts 4 modifications
- [ ] **SC-002**: 4+ recipes produce enhanced outputs
- [ ] **SC-003**: Each enhanced JSON has `modifications_applied` with attribution
- [ ] **SC-004**: Pipeline completes on all 6 recipes without error
- [ ] **SC-005**: Structured JSON log emitted per recipe

## Troubleshooting

### API Key Error
```
AuthenticationError: Invalid API key
```
→ Export valid key: `export OPENAI_API_KEY=sk-proj-...`

### Import Error
```
ModuleNotFoundError: No module named 'llm_pipeline'
```
→ Run from repo root: `cd /path/to/casper-studios-challenge`

### Rate Limit
```
RateLimitError: Rate limit exceeded
```
→ Wait 60s and retry. Consider adding delay between recipes.

## Related Artifacts

- **Data Model**: `.specify/memory/data-model.md`
- **Contracts**: `.specify/memory/contracts/`
- **Full Spec**: `.specify/memory/spec.md`
- **Implementation Plan**: `.specify/memory/plan.md`
