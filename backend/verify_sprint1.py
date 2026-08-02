import sqlite3, json

conn = sqlite3.connect('quiz_generator.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check 1: All questions have new fields populated
cur.execute('SELECT COUNT(*) as total FROM questions')
total = cur.fetchone()['total']

cur.execute('SELECT COUNT(*) as ok FROM questions WHERE type IS NOT NULL AND payload IS NOT NULL AND answer_key IS NOT NULL')
ok = cur.fetchone()['ok']

print('--- CHECK 1: Backfill completeness ---')
print('  Total questions :', total)
print('  Fully migrated  :', ok)
print('  Status          :', 'PASS' if total == ok else 'FAIL - missing rows!')

# Check 2: Spot-check payload and answer_key shape
cur.execute('SELECT id, type, payload, answer_key, options, correct_option FROM questions LIMIT 3')
rows = cur.fetchall()
print()
print('--- CHECK 2: Spot-check 3 rows ---')
all_ok = True
for row in rows:
    p = json.loads(row['payload'])
    a = json.loads(row['answer_key'])
    shape_ok  = 'options' in p and 'correct_index' in a
    compat_ok = row['options'] is not None and row['correct_option'] is not None
    status = 'PASS' if (shape_ok and compat_ok) else 'FAIL'
    if status == 'FAIL':
        all_ok = False
    print('  Q#' + str(row['id']) + ' type=' + str(row['type']) + ' payload_ok=' + str(shape_ok) + ' old_cols_ok=' + str(compat_ok) + ' -> ' + status)

print()
overall = 'PASS - Sprint 1 DB state is correct' if (total == ok and all_ok) else 'FAIL - issues found!'
print('--- RESULT:', overall, '---')
conn.close()
