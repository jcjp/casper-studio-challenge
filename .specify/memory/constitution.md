<!--
Sync Impact Report
Version change: 0.0.0 → 1.0.0
Added sections: Core Principles (5), Quality Standards, Development Workflow, Governance
Removed sections: None (initial creation)
Templates requiring updates: ✅ All aligned (initial setup)
Follow-up TODOs: None
-->

# Recipe Enhancement Pipeline Constitution

## Core Principles

### I. Correctness Over Speed
The pipeline MUST correctly parse and apply ALL discrete modifications from review text. A review stating "I added an egg and halved the sugar" contains TWO modifications—both MUST be extracted and applied. Partial extraction is a bug, not a feature.

### II. Transparency & Attribution
Every modification applied to a recipe MUST be traceable to its source review. Users MUST be able to inspect line-level diffs showing exactly what changed and why. No silent modifications.

### III. Robustness at Scale
The system MUST handle recipes beyond the initial 5 examples. Poor assumptions embedded in the implementation (hardcoded paths, magic numbers, format assumptions) MUST be identified and eliminated. The pipeline should gracefully handle edge cases: missing data, malformed reviews, conflicting modifications.

### IV. Test-Driven Validation
Changes to the pipeline MUST be validated against real recipe data. Before claiming a fix works, run it against ALL available recipes and verify outputs. Tests should cover: multi-modification parsing, fuzzy matching accuracy, modification application correctness.

### V. Incremental Progress
Given the 4-hour time constraint, prioritize high-impact fixes over comprehensive refactoring. Document what's fixed, what's broken, and what's deferred. Ship working improvements, not perfect architecture.

## Quality Standards

- Code changes MUST include verification against actual pipeline runs
- Enhanced recipe outputs MUST preserve all original recipe data not being modified
- LLM prompts MUST be structured to return ALL modifications, not just one category
- Fuzzy matching MUST log confidence scores and warn on low-confidence matches
- Error handling MUST be explicit—no silent failures

## Development Workflow

1. **Diagnose**: Run pipeline on all recipes, identify failure modes
2. **Prioritize**: Rank issues by impact (multi-mod parsing > edge cases)
3. **Fix**: Implement minimal changes that address root cause
4. **Verify**: Re-run pipeline, compare outputs
5. **Document**: Update analysis doc with findings and changes

## Governance

This constitution guides decision-making when implementation choices conflict. When in doubt:
- Correctness beats elegance
- Explicit beats implicit
- Working beats complete

**Version**: 1.0.0 | **Ratified**: 2026-09-08 | **Last Amended**: 2026-09-08
