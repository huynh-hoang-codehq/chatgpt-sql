dockerid=$(docker ps -aqf "name=chatgpt-sql-app")
docker logs --follow ${dockerid}