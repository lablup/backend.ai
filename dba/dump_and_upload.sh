# make dump file from db
pg_dump -U postgres backend | gzip > backend.sql.gz

# upload dump file to s3
# 
