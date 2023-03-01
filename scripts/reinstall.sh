docker rm -f collector
docker build --tag collector .
docker run --name collector -idt --volume ./app/:/root/ -p 80:3000 collector bash
#docker exec -it collector python3 -m ocr en