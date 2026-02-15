# 🐛 Frontend Real-time Updates - Debugging Guide

## Issue: Frontend not showing updates during repository processing

### ✅ What's Working:
- Backend is processing files successfully ✅
- Pull requests are being created ✅  
- Backend is completing without errors ✅

### ❌ What's Not Working:
- Frontend not receiving real-time updates from Supabase
- No file processing status visible during operation

---

## 🔍 Step-by-Step Debugging

### Step 1: Check Browser Console

1. Open your frontend: http://localhost:3000
2. Open DevTools (F12 or Cmd+Option+I)
3. Go to Console tab
4. Look for these messages:

**Expected Console Output:**
```
🔌 Setting up Supabase real-time subscription...
📡 Supabase subscription status: SUBSCRIBED
🚀 Starting repository processing...
📦 Repository URL: https://github.com/...
📨 Received update from Supabase: {...}
✨ New update: {status: "READING", message: "📖 Reading _app.js", ...}
📊 Current updates count: 2
```

**If you see:**
- ❌ `Subscription status: CHANNEL_ERROR` → Supabase config issue
- ❌ `Subscription status: TIMED_OUT` → Network/firewall issue
- ❌ No "Received update" messages → Real-time not enabled in Supabase

---

### Step 2: Verify Supabase Real-time is Enabled

1. Go to: https://kuxwmlxghamrslgbxiof.supabase.co
2. Click **Database** → **Replication**
3. Make sure `repo-updates` table has **"Realtime"** enabled
4. If not enabled:
   - Click the toggle next to `repo-updates`
   - Wait a few seconds
   - Try again

**Or run this SQL:**
```sql
-- Enable real-time for repo-updates
ALTER PUBLICATION supabase_realtime ADD TABLE "repo-updates";

-- Verify it's enabled
SELECT schemaname, tablename 
FROM pg_publication_tables 
WHERE pubname = 'supabase_realtime';
```

---

### Step 3: Check Network Tab

1. In DevTools, go to **Network** tab
2. Filter by `WS` (WebSocket)
3. Start a repository processing
4. You should see:
   - WebSocket connection to Supabase
   - Status: `101 Switching Protocols` (success)
   - Messages being sent/received

**If WebSocket fails:**
- Check if firewall is blocking WebSocket connections
- Try disabling browser extensions (adblockers)
- Check if you're behind a corporate proxy

---

### Step 4: Test Real-time Manually

**Option A: Browser Console Test**
```javascript
// Paste in browser console on http://localhost:3000
const { createClient } = require('@supabase/supabase-js');

const testClient = createClient(
  'https://kuxwmlxghamrslgbxiof.supabase.co',
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt1eHdtbHhnaGFtcnNsZ2J4aW9mIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMyMTU4NjcsImV4cCI6MjA3ODc5MTg2N30.LF2VtyFhC_gAqj0jJyBE5bcfYmPcIHOt5kmJCO0wETc'
);

testClient
  .channel('test')
  .on('postgres_changes', 
    { event: '*', schema: 'public', table: 'repo-updates' },
    (payload) => console.log('Got update!', payload)
  )
  .subscribe((status) => console.log('Status:', status));
```

**Option B: Manual Insert Test**

1. Go to Supabase → **Table Editor** → `repo-updates`
2. Click **Insert** → **Insert row**
3. Add:
   ```json
   {
     "status": "TESTING",
     "message": "Test message",
     "code": "console.log('test')"
   }
   ```
4. Click **Save**
5. Check if frontend console shows the update

---

### Step 5: Check Environment Variables

**Frontend `.env.local` should have:**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://kuxwmlxghamrslgbxiof.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_URL=http://localhost:5001
```

**Verify they're loaded:**
```javascript
// In browser console
console.log(process.env.NEXT_PUBLIC_SUPABASE_URL);
console.log(process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
```

If `undefined`, restart Next.js dev server:
```bash
cd frontend
npm run dev
```

---

### Step 6: Check Row Level Security (RLS)

The issue might be RLS policies blocking anonymous reads.

**Run this SQL to check:**
```sql
-- Check if RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'repo-updates';

-- Check policies
SELECT * FROM pg_policies 
WHERE tablename = 'repo-updates';
```

**Expected policies:**
- `Allow service role full access` (for backend)
- `Allow authenticated read` (for frontend)

**If missing, add:**
```sql
-- Allow anonymous reads (for real-time)
CREATE POLICY "Allow anonymous read on repo-updates"
  ON "repo-updates" FOR SELECT
  TO anon
  USING (true);
```

---

### Step 7: Check CORS

If requests are being blocked:

1. Check browser console for CORS errors
2. Verify backend CORS settings in `server.py`:
   ```python
   allow_origins=['http://localhost:3000']
   ```

---

## 🎯 Quick Fixes

### Fix 1: Disable RLS Temporarily (Testing Only!)
```sql
ALTER TABLE "repo-updates" DISABLE ROW LEVEL SECURITY;
```
⚠️ Re-enable after testing!

### Fix 2: Add Anon Policy
```sql
CREATE POLICY "Allow anon read on repo-updates"
  ON "repo-updates" FOR SELECT
  TO anon
  USING (true);
```

### Fix 3: Restart Everything
```bash
# Stop backend (Ctrl+C)
# Stop frontend (Ctrl+C)

# Clear Next.js cache
cd frontend
rm -rf .next

# Restart backend
cd ../backend
uvicorn server:app --reload --port 5001

# Restart frontend (new terminal)
cd ../frontend
npm run dev
```

### Fix 4: Use Polling as Fallback

If real-time doesn't work, add polling in `MainDash.tsx`:

```typescript
useEffect(() => {
  if (!isLoading) return;
  
  const interval = setInterval(async () => {
    const { data } = await supabase
      .from('repo-updates')
      .select('*')
      .order('created_at', { ascending: true });
    
    if (data) {
      console.log('📊 Polled data:', data);
      setUpdates(data);
    }
  }, 2000); // Poll every 2 seconds
  
  return () => clearInterval(interval);
}, [isLoading]);
```

---

## 📊 Expected Flow

1. User enters GitHub URL and clicks Enter
2. Frontend logs: `🚀 Starting repository processing...`
3. Frontend calls backend `/update` endpoint
4. Backend starts processing
5. Backend inserts to `repo-updates` table:
   - `READING` status for each file
   - `WRITING` status with refactored code
   - `LOADING` status during git operations
6. Supabase real-time broadcasts changes
7. Frontend receives updates via WebSocket
8. Frontend displays:
   - File status panel
   - Live code preview
   - Old vs new comparison (when finished)

---

## 🆘 Still Not Working?

**Check this:**
1. ✅ Supabase real-time enabled for `repo-updates`?
2. ✅ RLS policy allows `anon` role to SELECT?
3. ✅ WebSocket connection established in Network tab?
4. ✅ Console shows "Subscription status: SUBSCRIBED"?
5. ✅ Backend is actually inserting to database?
6. ✅ Environment variables loaded in frontend?

**Collect these logs and share:**
- Browser console output
- Network tab WebSocket traffic
- Backend terminal output
- Supabase policies output

---

## 💡 Pro Tips

- Open browser console BEFORE clicking Enter
- Watch for the subscription status message
- Check if you see "Received update" messages
- Verify the updates count increases
- Look at the debug panel in the UI

**The debug panel shows:**
- Updates Count
- Latest Status
- Latest Message  
- Supabase Connected status

This will help identify exactly where the issue is!
