-- ============================================================
-- FIX REAL-TIME UPDATES - Allow Anonymous Reads
-- ============================================================
-- This is likely why your frontend isn't seeing updates!
-- Run this in Supabase SQL Editor
-- ============================================================

-- Check current RLS status
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'repo-updates';

-- Check existing policies
SELECT policyname, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'repo-updates';

-- ============================================================
-- FIX: Add policy to allow anonymous (anon) reads
-- ============================================================
-- The frontend uses the ANON key, so it needs read permission!

CREATE POLICY "Allow anon read on repo-updates"
  ON "repo-updates" FOR SELECT
  TO anon
  USING (true);

-- ============================================================
-- Verify the policy was created
-- ============================================================
SELECT policyname, roles, cmd 
FROM pg_policies 
WHERE tablename = 'repo-updates'
ORDER BY policyname;

-- ============================================================
-- Expected output should include:
-- ============================================================
-- policyname                              | roles              | cmd
-- ----------------------------------------+--------------------+--------
-- Allow anon read on repo-updates        | {anon}             | SELECT
-- Allow authenticated read on repo-updates| {authenticated}    | SELECT
-- Allow service role full access ...     | {service_role}     | ALL
-- ============================================================

-- ============================================================
-- Alternative: Disable RLS for testing (NOT for production!)
-- ============================================================
-- Only use this temporarily to test if RLS is the issue
-- ALTER TABLE "repo-updates" DISABLE ROW LEVEL SECURITY;

-- Re-enable when done testing:
-- ALTER TABLE "repo-updates" ENABLE ROW LEVEL SECURITY;
-- ============================================================

-- ============================================================
-- Test real-time is working
-- ============================================================
-- After running this, insert a test row:
INSERT INTO "repo-updates" (status, message, code)
VALUES ('TEST', 'Testing real-time', 'console.log("test")');

-- Check if your frontend console shows this update!
-- Then delete the test row:
-- DELETE FROM "repo-updates" WHERE status = 'TEST';
-- ============================================================
