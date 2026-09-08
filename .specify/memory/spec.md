# Feature Specification: Recipe Enhancement Pipeline Fix

**Feature Branch**: `fix/multi-modification-parsing`

**Created**: 2026-09-08

**Status**: Draft

**Input**: Validate and fix the recipe enhancement pipeline to correctly parse ALL modifications from reviews

## Clarifications

### Session 2026-09-08

- Q: When multiple reviews suggest conflicting modifications to the same ingredient, how should conflicts be resolved? → A: Highest-rated review wins - apply modification from review with highest star rating
- Q: When the OpenAI API call fails, what's the recovery strategy? → A: Retry 3x then skip, log warning, record to DLQ for reprocessing
- Q: Should extracted modifications be validated against actual recipe ingredients before applying? → A: Fuzzy-match with threshold (0.6), accept if similarity >= threshold, log confidence
- Q: Should there be a cost/time budget per recipe? → A: Max 10 LLM calls per recipe, skip remaining reviews if exceeded
- Q: Should the pipeline emit structured logs/metrics for observability? → A: Structured JSON summary log per recipe run

## Problem Analysis

### Current State

The existing pipeline has several critical issues discovered during code review:

1. **Single Modification Extraction**: `tweak_extractor.py:extract_single_modification()` selects ONE random review and extracts ONE modification. Reviews often contain MULTIPLE discrete modifications (e.g., "I added an egg AND halved the sugar" = 2 modifications).

2. **Schema Limitation**: `ModificationObject` model has a single `modification_type` field, forcing multi-category changes into one bucket.

3. **Discrepancy in Demo Data**: The existing `data/enhanced/` files show 2+ modifications applied, but the actual code only processes 1 per run. Demo data was manually crafted or generated differently.

4. **Untested at Scale**: Only 2 of 6 recipes have enhanced outputs. 2 recipes have 0 reviews with modifications.

5. **Fuzzy Matching Risks**: `similarity_threshold: 0.6` is low; `str.replace()` only replaces first occurrence.

### Evidence from Code

```
# pipeline.py:146-150 - Only processes ONE review
modification, source_review = (
    self.tweak_extractor.extract_single_modification(reviews, recipe)
)
```

```
# prompts.py - Schema forces single modification_type
"modification_type": "quantity_adjustment|ingredient_substitution|technique_change|addition|removal"
```

### Evidence from Data

Example review with 4 modifications (only 2 were captured):
> "(1) I used a half cup of sugar and one-and-a-half cups of brown sugar; (2) I omitted the water; (3) I added a teaspoon of cream of tartar to the batter; (4) I refrigerated the batter for at least an hour"

Missing from enhanced output: water omission, cream of tartar addition, refrigeration step.

## User Scenarios & Testing

### User Story 1 - Multi-Modification Extraction (Priority: P1)

When a review contains multiple discrete modifications, the system extracts and applies ALL of them, not just the first or a random subset.

**Why this priority**: This is the core bug. Without this fix, the pipeline fundamentally doesn't work as intended.

**Independent Test**: Run pipeline on chocolate chip cookie recipe, verify ALL 4 modifications from the featured review are captured.

**Acceptance Scenarios**:

1. **Given** a review "I added an egg and halved the sugar", **When** extracted, **Then** returns 2 separate modifications: one addition, one quantity_adjustment
2. **Given** a review with numbered tweaks (1), (2), (3), (4), **When** extracted, **Then** returns 4 modifications
3. **Given** a review with no modifications, **When** processed, **Then** gracefully skips without error

---

### User Story 2 - Process All Reviews (Priority: P2)

Process all reviews with modifications for a recipe, not just one random one.

**Why this priority**: Even if we extract all modifications from ONE review, we're still missing modifications from OTHER reviews.

**Independent Test**: Run pipeline on a recipe with 4 modification reviews, verify output contains modifications from all 4.

**Acceptance Scenarios**:

1. **Given** a recipe with 4 reviews marked `has_modification: true`, **When** processed, **Then** all 4 reviews are analyzed
2. **Given** conflicting modifications across reviews, **When** processed, **Then** modification from highest-rated review is applied

---

### User Story 3 - Scale Beyond 5 Examples (Priority: P3)

Pipeline handles all 6 sample recipes, including edge cases.

**Why this priority**: Validates robustness beyond happy path.

**Independent Test**: Run `test_pipeline.py all`, verify 4+ recipes produce valid enhanced outputs.

**Acceptance Scenarios**:

1. **Given** recipe with 0 reviews, **When** processed, **Then** logs warning and returns None gracefully
2. **Given** recipe with malformed ingredient format, **When** fuzzy matching fails, **Then** logs specific mismatch details

---

### Edge Cases

- Review mentions modification but provides no actionable detail ("I changed something and it was great!")
- Modification references ingredient not in recipe (typo or recipe variation) - fuzzy-match at 0.6 threshold; if score < 0.6, skip modification and log warning with confidence score
- Multiple reviews suggest conflicting changes to same ingredient - highest-rated review wins
- Review modification is actually a technique change disguised as ingredient change
- Recipe has >10 modification reviews - process first 10 by rating, skip remainder

## Requirements

### Functional Requirements

- **FR-001**: System MUST extract ALL discrete modifications from a single review text
- **FR-002**: System MUST process ALL reviews with `has_modification: true`, not just one random one
- **FR-003**: System MUST support multiple `modification_type` values per review extraction
- **FR-004**: System MUST log which modifications were successfully applied vs. failed
- **FR-005**: System MUST preserve original recipe data for fields not being modified
- **FR-006**: System MUST handle recipes with 0 modification reviews gracefully
- **FR-007**: System MUST resolve conflicts by applying modification from highest-rated review; on equal ratings, most recent review wins
- **FR-008**: System MUST validate extracted modifications against recipe ingredients using fuzzy matching (threshold 0.6)
- **FR-009**: System MUST limit LLM calls to max 10 per recipe to control costs
- **FR-010**: System MUST record failed extractions to DLQ for reprocessing (FUTURE - not in current scope)

### Non-Functional Requirements

- **NFR-001**: System MUST emit structured JSON summary log per recipe run (modifications extracted, applied, failed, processing time)
- **NFR-002**: System MUST retry failed LLM calls 3x before skipping
- **NFR-003**: System MUST log confidence scores for fuzzy matches

### Key Entities

- **ModificationObject**: Currently single-type; needs to support multiple edits across categories OR return array
- **EnhancedRecipe**: Already supports `modifications_applied: List[ModificationApplied]` - schema is fine
- **Review**: Has `has_modification` flag - may need validation that flag is accurate
<!-- FUTURE: Define DLQ Entry schema when FR-010 is implemented: review_id, recipe_id, error_type, error_message, timestamp, retry_count -->

## Success Criteria

### Measurable Outcomes

- **SC-001**: Pipeline extracts 4 modifications from the "numbered tweaks" chocolate chip review (currently extracts 2)
- **SC-002**: All 4 recipes with modifications produce enhanced outputs (currently 2)
- **SC-003**: Enhanced output JSON includes attribution for every applied modification
- **SC-004**: Pipeline completes without errors on all 6 sample recipes
- **SC-005**: Structured JSON log emitted for each recipe run with extraction/application metrics

## Assumptions

- LLM (gpt-3.5-turbo) can reliably extract multiple modifications when prompted correctly
- Existing fuzzy matching threshold (0.6) is acceptable for ingredient matching
- Reviews marked `has_modification: true` actually contain modifications (scraped data is accurate)
- Time constraint (4 hours) means we fix extraction, defer UI/deployment concerns
- Demo enhanced JSON files can be regenerated; no need to preserve them
- Reviews are processed in descending rating order for conflict resolution
