# Test Results

Pipeline validation run: 2026-09-08

## Summary

| Metric | Value |
|--------|-------|
| Recipes processed | 4/6 |
| Total modifications | 26 |
| Total changes | 24 |
| Success rate | 100% (4/4 with mod reviews) |

## Enhanced Recipes

| Recipe | Mods | Changes | Status |
|--------|------|---------|--------|
| Best Chocolate Chip Cookies | 11 | 13 | ✅ |
| Creamy Sweet Potato Soup | 9 | 7 | ✅ |
| Spicy Apple Cake | 3 | 3 | ✅ |
| Nikujaga | 3 | 1 | ✅ |
| Mango Teriyaki Marinade | - | - | ⏭️ (0 mod reviews) |
| Spiced Purple Plum Jam | - | - | ⏭️ (0 mod reviews) |

## Success Criteria Validation

- **SC-001**: Chocolate chip "4 tweaks" review → 4 modifications ✅
- **SC-002**: 4+ recipes enhanced → 4 ✅
- **SC-003**: All mods have `source_review` attribution ✅
- **SC-004**: Pipeline runs on all 6 recipes without error ✅
- **SC-005**: Structured JSON logs emitted ✅

## Files

- `pipeline_summary_report.json` - Aggregate stats
- `enhanced_*.json` - Individual enhanced recipes with full attribution
