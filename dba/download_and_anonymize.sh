# download dump file from s3

# create new db and restore by dump
createdb -U postgres backend_dump
gunzip -c backend.sql.gz | psql backend

# anonymize restored db
psql -U postgres backend < anonymize_db.sql
