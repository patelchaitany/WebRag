# Quick Fix for UNIQUE Constraint Error

## TL;DR - 3 Steps to Fix

### Step 1: Stop Everything
```bash
# Kill the worker and API
Ctrl+C
```

### Step 2: Run Migration
```bash
python fix_database.py
```

### Step 3: Restart
```bash
# Terminal 1
python app.py

# Terminal 2
python ingestion_worker.py
```

Done! ✅

---

## What Was Fixed

| Issue | Fix |
|-------|-----|
| Duplicate FAISS IDs on retry | Delete old chunks before reprocessing |
| UNIQUE constraint violation | Made `faiss_id` nullable in database |
| Reprocessing same URL fails | Automatic cleanup implemented |

---

## Files Changed

1. **ingestion_worker.py** - Added chunk deletion logic
2. **models.py** - Made faiss_id nullable
3. **fix_database.py** - New migration script (run once)

---

## Verify It Works

```bash
# Test 1: Ingest URL
curl -X POST http://localhost:5000/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://codeforces.com/contest/2154/problem/C"}'

# Wait 5-10 seconds...

# Test 2: Query
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this problem about?", "top_k": 5}'

# Test 3: Re-ingest same URL (should work now!)
curl -X POST http://localhost:5000/ingest-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://codeforces.com/contest/2154/problem/C"}'
```

---

## Backup Info

Your database backup is at:
```
./data/rag.db.backup_YYYYMMDD_HHMMSS
```

If needed, restore with:
```bash
cp ./data/rag.db.backup_* ./data/rag.db
```

---

## Still Having Issues?

Check logs:
```bash
tail -f ./logs/app.log
```

See detailed guide: `UNIQUE_CONSTRAINT_FIX.md`

