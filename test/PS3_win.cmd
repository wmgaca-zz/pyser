SELECT COUNT DISTINCT '\d+' FROM (
  SELECT '[xyzw]+\s+\d+' FROM (
    SELECT '\/\/ [A-Z]+[a-zA-Z_]+\s+\d+[\s+\w+\d+]+\n' FROM (
      SELECT 'Input.*Output'
    )
  )
)
