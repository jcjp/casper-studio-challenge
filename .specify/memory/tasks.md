# Tasks: Recipe Enhancement Pipeline Fix

**Branch**: `fix/multi-modification-parsing` | **Date**: 2026-09-08

**Source Documents**: spec.md, plan.md, data-model.md, contracts/, quickstart.md

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US1/US2/US3]**: Which user story this task belongs to

---

## Phase 1: Setup

**Purpose**: Verify environment and understand current state

- [ ] T001 Verify Python 3.13 and dependencies installed via `pip install -r requirements.txt`
- [ ] T002 Verify OpenAI API key configured via `echo $OPENAI_API_KEY | head -c 10`
- [ ] T003 Run existing pipeline to establish baseline via `python src/test_pipeline.py single 10813`
- [ ] T004 Document current behavior (how many mods extracted?) in scratch notes

---

## Phase 2: Foundational (Schema & Prompt Changes)

**Purpose**: Core infrastructure changes that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Add `ModificationList` Pydantic model in `src/llm_pipeline/models.py`
- [x] T006 Update `build_simple_prompt()` to request array of modifications in `src/llm_pipeline/prompts.py`
- [x] T007 Update `extract_modification()` to parse array response in `src/llm_pipeline/tweak_extractor.py`
- [x] T008 Add robust JSON array parsing; if LLM returns single object, wrap in array (not revert to old behavior) in `src/llm_pipeline/tweak_extractor.py`

**Checkpoint**: LLM now returns array of modifications from single review

---

## Phase 3: User Story 1 - Multi-Modification Extraction (Priority: P1) MVP

**Goal**: Extract ALL discrete modifications from a single review text

**Independent Test**: Run on chocolate chip recipe, verify 4 modifications from numbered review

### Implementation

- [ ] T009 [US1] Test extraction with "4 tweaks" review manually via Python REPL
- [ ] T010 [US1] Verify 4 distinct `ModificationObject` instances returned
- [x] T011 [US1] Add logging for each modification extracted in `src/llm_pipeline/tweak_extractor.py`
- [x] T012 [US1] Handle edge case: review with no actionable modifications returns empty list

**Checkpoint**: Single review correctly yields ALL modifications (SC-001 met)

---

## Phase 4: User Story 2 - Process All Reviews (Priority: P2)

**Goal**: Process ALL reviews with `has_modification: true`, not just one random one

**Independent Test**: Run on recipe with 4 modification reviews, verify all 4 analyzed

### Implementation

- [x] T013 [US2] Rename `extract_single_modification()` to `extract_all_modifications()` in `src/llm_pipeline/tweak_extractor.py`
- [x] T014 [US2] Loop through all `has_modification` reviews in `extract_all_modifications()`
- [x] T015 [US2] Sort reviews by rating descending for conflict resolution (FR-007)
- [x] T016 [US2] Aggregate modifications from all reviews into single list
- [x] T017 [US2] Add LLM call limit (max 10 per recipe) per FR-009 in `src/llm_pipeline/tweak_extractor.py`
- [x] T018 [US2] Update `process_single_recipe()` to call new method in `src/llm_pipeline/pipeline.py`
- [x] T019 [US2] Log which reviews were processed and which skipped

**Checkpoint**: All modification reviews analyzed, highest-rated wins conflicts (SC-002 partial)

---

## Phase 5: User Story 3 - Scale Beyond 5 Examples (Priority: P3)

**Goal**: Pipeline handles all 6 sample recipes including edge cases

**Independent Test**: Run `python src/test_pipeline.py all`, verify 4+ valid outputs

### Implementation

- [x] T020 [US3] Handle recipe with 0 modification reviews gracefully in `src/llm_pipeline/pipeline.py`
- [x] T021 [US3] Log warning for recipes with no modifications (don't error)
- [x] T022 [US3] Improve fuzzy matching logging with confidence scores in `src/llm_pipeline/recipe_modifier.py`
- [x] T023 [US3] Add retry logic (3x) for failed LLM calls per NFR-002 in `src/llm_pipeline/tweak_extractor.py`
- [x] T024 [US3] Add structured JSON summary log per recipe run per NFR-001 in `src/llm_pipeline/pipeline.py`
- [ ] T025 [US3] Run pipeline on all 6 recipes, fix any remaining edge case failures
- [ ] T025a [US3] Verify non-modified recipe fields (title, description, cook_time, etc.) preserved in enhanced output

**Checkpoint**: 4+ recipes produce valid enhanced output (SC-002, SC-004 met)

---

## Phase 6: Polish & Documentation

**Purpose**: Final verification, documentation, and cleanup

- [ ] T026 [P] Verify quickstart.md validation scenarios pass
- [x] T027 [P] Write `ANALYSIS.md` documenting problems found and solutions
- [x] T028 [P] Document technical decisions and trade-offs in `ANALYSIS.md`
- [x] T029 [P] List future improvements in `ANALYSIS.md`
- [ ] T030 Verify all success criteria met (SC-001 through SC-005)
- [ ] T030a Verify every `modifications_applied` entry has valid `source_review` attribution
- [ ] T031 Clean up any debug logging or temporary code
- [ ] T032 Commit changes with clear commit message

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) -> Phase 2 (Foundational) -> Phase 3-5 (User Stories) -> Phase 6 (Polish)
```

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational
- **User Story 2 (Phase 4)**: Depends on User Story 1 (builds on extraction changes)
- **User Story 3 (Phase 5)**: Depends on User Story 2 (validates full pipeline)
- **Polish (Phase 6)**: Depends on all user stories

### File-Level Dependencies

| File | Depends On | Touches |
|------|------------|---------|
| `models.py` | None | T005 |
| `prompts.py` | models.py | T006 |
| `tweak_extractor.py` | models.py, prompts.py | T007-T008, T011-T017, T023 |
| `pipeline.py` | tweak_extractor.py | T018, T020-T021, T024 |
| `recipe_modifier.py` | None | T022 |

### Parallel Opportunities

Within Phase 2 (Foundational):
```
T005 (models.py) + T006 (prompts.py) can run in parallel
T007-T008 (tweak_extractor.py) must wait for T005+T006
```

Within Phase 6 (Polish):
```
T026 + T027 + T028 + T029 can all run in parallel
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T008)
3. Complete Phase 3: User Story 1 (T009-T012)
4. **VALIDATE**: Chocolate chip review extracts 4 modifications
5. This alone delivers core value - pipeline extracts ALL mods from ONE review

### Incremental Delivery

| Milestone | Tasks | Validation |
|-----------|-------|------------|
| Baseline | T001-T004 | Know current state |
| Schema Ready | T005-T008 | LLM returns arrays |
| MVP (US1) | T009-T012 | 4 mods from 1 review |
| US2 Complete | T013-T019 | All reviews processed |
| US3 Complete | T020-T025a | 4+ recipes work |
| Ship | T026-T032 | ANALYSIS.md complete |

### Time Budget (4 hours)

| Phase | Est. Time | Cumulative |
|-------|-----------|------------|
| Setup | 15 min | 0:15 |
| Foundational | 45 min | 1:00 |
| User Story 1 | 30 min | 1:30 |
| User Story 2 | 45 min | 2:15 |
| User Story 3 | 45 min | 3:00 |
| Polish | 60 min | 4:00 |

---

## Notes

- No automated tests requested - validation via manual pipeline runs
- `enhanced_recipe_generator.py` already supports multiple modifications
- Focus on extraction fix first (biggest impact)
- Conflict resolution: highest-rated review wins; on tie, most recent review wins
- Max 10 LLM calls per recipe to control costs
- FUTURE: Implement DLQ (Dead Letter Queue) for failed extractions per FR-010
