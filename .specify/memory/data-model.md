# Data Model: Recipe Enhancement Pipeline

**Version**: 1.0.0 | **Date**: 2026-09-08 | **Spec**: `.specify/memory/spec.md`

## Entity Relationship Diagram

```
┌─────────────┐     1:N      ┌────────────┐
│   Recipe    │──────────────│   Review   │
└─────────────┘              └────────────┘
       │                           │
       │ 1:1                       │ extracts
       ▼                           ▼
┌─────────────────┐    N:1   ┌──────────────────┐
│ EnhancedRecipe  │◄─────────│ ModificationList │
└─────────────────┘          └──────────────────┘
       │                           │
       │ 1:N                       │ contains
       ▼                           ▼
┌────────────────────┐       ┌────────────────────┐
│ ModificationApplied│       │ ModificationObject │
└────────────────────┘       └────────────────────┘
       │                           │
       │ 1:N                       │ 1:N
       ▼                           ▼
┌──────────────┐             ┌──────────────────┐
│ ChangeRecord │             │ ModificationEdit │
└──────────────┘             └──────────────────┘
```

## Core Entities

### Recipe (Input)

Source recipe data scraped from AllRecipes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| recipe_id | string | ✓ | Unique identifier (e.g., "10813") |
| title | string | ✓ | Recipe name |
| ingredients | List[string] | ✓ | Ingredient list with quantities |
| instructions | List[string] | ✓ | Step-by-step preparation |
| description | string | | Recipe summary |
| servings | string | | Number of servings |
| rating | object | | { value: string, count: string } |
| preptime | string | | ISO 8601 duration |
| cooktime | string | | ISO 8601 duration |
| totaltime | string | | ISO 8601 duration |

**Validation Rules**:
- `recipe_id` must be non-empty alphanumeric
- `ingredients` must have at least 1 item
- `instructions` must have at least 1 step

---

### Review (Input)

User review associated with a recipe.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | ✓ | Full review text |
| rating | int | | Star rating (1-5) |
| username | string | | Reviewer identifier |
| has_modification | bool | ✓ | Flag: contains actionable modification |

**Validation Rules**:
- `text` must be non-empty
- `rating` if present must be 1-5
- `has_modification` determines if review is processed

---

### ModificationObject (Extracted)

Single modification parsed from review text by LLM.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| modification_type | enum | ✓ | Category: ingredient_substitution, quantity_adjustment, technique_change, addition, removal |
| reasoning | string | ✓ | Why this modification improves recipe |
| edits | List[ModificationEdit] | ✓ | Atomic edit operations |

**Validation Rules**:
- `modification_type` must be valid enum value
- `edits` must have at least 1 item

---

### ModificationList (NEW - To Be Added)

Array wrapper for multiple modifications from a single review.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| modifications | List[ModificationObject] | ✓ | All modifications from one review |
| source_review | SourceReview | ✓ | Reference to originating review |

**Validation Rules**:
- Can be empty (review has no actionable modifications)
- Each item must be valid ModificationObject

---

### ModificationEdit (Extracted)

Atomic edit operation within a modification.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| target | enum | ✓ | "ingredients" or "instructions" |
| operation | enum | ✓ | "replace", "add_after", or "remove" |
| find | string | ✓ | Text to locate in recipe |
| replace | string | cond | Required for "replace" operation |
| add | string | cond | Required for "add_after" operation |

**Validation Rules**:
- `find` must be non-empty
- `replace` required when operation="replace"
- `add` required when operation="add_after"

---

### EnhancedRecipe (Output)

Recipe with community modifications applied.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| recipe_id | string | ✓ | Enhanced recipe ID (format: "enhanced_{original_id}") |
| original_recipe_id | string | ✓ | Reference to source recipe |
| title | string | ✓ | Enhanced recipe title |
| ingredients | List[string] | ✓ | Modified ingredients |
| instructions | List[string] | ✓ | Modified instructions |
| modifications_applied | List[ModificationApplied] | ✓ | Full audit trail |
| enhancement_summary | EnhancementSummary | ✓ | High-level summary |
| created_at | string | ✓ | ISO 8601 timestamp |
| pipeline_version | string | ✓ | Pipeline version tag |

**Validation Rules**:
- `modifications_applied` must have at least 1 item (otherwise no enhancement occurred)
- All original recipe metadata fields preserved

---

### ModificationApplied (Output)

Record of modification successfully applied.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| source_review | SourceReview | ✓ | Review attribution |
| modification_type | string | ✓ | Category applied |
| reasoning | string | ✓ | Justification |
| changes_made | List[ChangeRecord] | ✓ | Detailed change log |

---

### ChangeRecord (Output)

Individual change made to recipe.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | enum | ✓ | "ingredient" or "instruction" |
| from_text | string | ✓ | Original text |
| to_text | string | ✓ | Modified text |
| operation | enum | ✓ | "replace", "add", or "remove" |

---

### DLQEntry (NEW - To Be Added)

Dead-letter queue entry for failed extractions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| recipe_id | string | ✓ | Source recipe |
| review_text | string | ✓ | Review that failed extraction |
| error_type | string | ✓ | Classification: parse_error, api_error, validation_error |
| error_message | string | ✓ | Detailed error |
| timestamp | string | ✓ | ISO 8601 when failure occurred |
| retry_count | int | ✓ | Number of retries attempted |

## State Transitions

### Modification Lifecycle

```
Review.text → [LLM Extract] → ModificationObject[] → [Apply] → ModificationApplied
                    │                                    │
                    ▼                                    ▼
              DLQEntry (on failure)              ChangeRecord[]
```

### Recipe Processing States

```
                    ┌──────────────┐
                    │   PENDING    │ Recipe loaded, not processed
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  EXTRACTING  │ Reviews being analyzed
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  NO_MODS    │ │  APPLYING   │ │   ERROR     │
    │  (terminal) │ │             │ │  (to DLQ)   │
    └─────────────┘ └──────┬──────┘ └─────────────┘
                           │
                    ┌──────▼───────┐
                    │  COMPLETED   │ Enhanced recipe written
                    └──────────────┘
```

## Fuzzy Matching Rules

For ingredient matching (FR-008):

| Scenario | Action |
|----------|--------|
| Similarity ≥ 0.8 | Auto-match, high confidence |
| 0.6 ≤ Similarity < 0.8 | Match with warning log |
| Similarity < 0.6 | No match, log to DLQ |

## Conflict Resolution (FR-007)

When multiple reviews modify same ingredient:

1. Sort reviews by `rating` descending
2. Apply modifications in order
3. Later modifications win on overlap
4. Log all conflicts for transparency
