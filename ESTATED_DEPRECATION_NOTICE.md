# Estated API Deprecation Notice

## Important Update

**Estated API is being deprecated in 2026** and migrated to ATTOM infrastructure.

## What This Means

### Timeline
- **2025**: Estated API continues to work, but documentation won't be maintained
- **2026**: Estated documentation will be deprecated (exact date TBD)
- **Future**: All functionality will be available through ATTOM

### Impact on Your Project

Since you're **already using ATTOM** as your primary data source:

1. **Estated may become redundant** - ATTOM is merging Estated's data sources
2. **No immediate action required** - Your existing Estated API keys will remain valid
3. **No downtime expected** - Migration will be seamless
4. **Consider removing Estated** - Once ATTOM migration is complete

## Recommendations

### Short Term (Now)
1. ✅ **Keep Estated enabled** - It still works and can fill data gaps
2. ✅ **Monitor ATTOM updates** - They may be improving data completeness
3. ✅ **Test ATTOM data quality** - Check if missing fields are now available

### Medium Term (2025)
1. **Compare data sources** - See if ATTOM now has the data Estated provides
2. **Reduce Estated usage** - Only use when absolutely necessary
3. **Monitor migration status** - Check ATTOM for updates

### Long Term (2026+)
1. **Remove Estated dependency** - Once ATTOM migration is complete
2. **Update documentation** - Remove Estated references
3. **Rely on ATTOM + Estimation** - Your primary data sources

## What to Do

### Option 1: Keep Estated (Recommended for Now)
- Continue using Estated as fallback
- Monitor ATTOM data improvements
- Plan to remove in 2026

### Option 2: Disable Estated Now
- Set `ESTATED_ENABLED=false` in `.env`
- Rely on ATTOM + estimation
- Test if data quality is acceptable

### Option 3: Check ATTOM First
- Test if ATTOM has improved their data
- Contact ATTOM support: https://www.attomdata.com/contact-us/
- Ask about Estated data migration timeline

## Current Data Flow

```
1. ATTOM API (Primary)
   ↓ (if missing data)
2. Estated API (Fallback - deprecated 2026)
   ↓ (if still missing)
3. Estimation from square footage
```

## Future Data Flow (After Migration)

```
1. ATTOM API (Primary - includes Estated data)
   ↓ (if still missing)
2. Estimation from square footage
```

## Questions?

- **ATTOM Support**: https://www.attomdata.com/contact-us/
- **Migration Status**: Check ATTOM documentation for updates
- **Timeline**: Exact deprecation date TBD (sometime in 2026)

## Code Changes Needed (Future)

When Estated is fully deprecated, you can:

1. Remove Estated from `config.py`:
   ```python
   # Remove these lines:
   estated_api_key: str = ""
   estated_enabled: bool = False
   ```

2. Remove Estated fallback from `bot.py`:
   ```python
   # Remove the Estated API fallback section
   ```

3. Update documentation:
   - Remove `ESTATED_SETUP.md`
   - Update `DATA_COMPLETENESS_GUIDE.md`
   - Update `ESTATED_DEPRECATION_NOTICE.md` (mark as complete)

## Summary

- ✅ **No immediate action required** - Estated still works
- ⚠️ **Plan for 2026** - Estated will be deprecated
- 🎯 **Focus on ATTOM** - They're your primary source anyway
- 📊 **Monitor improvements** - ATTOM may have better data now

