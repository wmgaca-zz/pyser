SELECT SUM FROM (
  SELECT COUNT EACH DISTINCT EACH '[xyzw]+' FROM (
    SELECT 'cb0\[\d+\].[xyzw]+' FROM (
      SELECT 'mad[ a-zA-Z0-9-,\.\[\]]+'
    )
  )
)
