#!/bin/bash
# Apply Database Migration Helper Script
# Copies migration SQL to clipboard and opens Supabase SQL Editor

echo "📋 Copying migration SQL to clipboard..."
cat backend/migrations/002_multi_leg_positions.sql | pbcopy

echo "✅ Migration SQL copied to clipboard!"
echo ""
echo "🌐 Opening Supabase SQL Editor..."
open "https://app.supabase.com/project/zwuqmnzqjkybnbicwbhz/sql/new"

echo ""
echo "📝 Next steps:"
echo "   1. Paste the SQL (Cmd+V) into the editor"
echo "   2. Click 'Run' (or press Cmd+Enter)"
echo "   3. Look for success message: ✅ 'Multi-leg position columns added successfully'"
echo ""
echo "⚠️  If you see an error, let me know and we'll troubleshoot!"
