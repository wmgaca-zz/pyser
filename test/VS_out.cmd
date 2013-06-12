SELECT COUNT 
FROM (
  SELECT '\/\/ [A-Z]+[a-zA-Z_]+\s+\d+\s+\w+\s+\d+\s+\w+\s+\w+\s+\w+\s*\r\n' 
  FROM (
    SELECT 'Output.*'
  )
)
