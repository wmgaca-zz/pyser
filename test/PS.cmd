SELECT '\d+' FROM (
  SELECT '\[\d+\]' FROM (
      SELECT 'dcl_constantbuffer cb0\[\d+\]'
  )
)
LIMIT 1
