SELECT SUM FROM (
  SELECT COUNT_EACH DISTINCT_EACH '[xyzw]+' FROM (
    SELECT DISTINCT 'cb0\[\d+\]\.[xyzw]+' FROM (
      SELECT 'mad[ a-zA-Z0-9-,\.\[\]]+\n'
    )
  )
)
