docker rm -f collector
docker build --tag collector .
docker run --name collector -idt --restart unless-stopped --volume ./app/:/root/ -p 80:3000 --env-file ./.env collector
#docker exec -it collector python3 -m ocr en