docker rm -f collector
docker build --tag collector .
docker run --name collector -idt --volume ./app/:/root/:ro collector
docker exec -it collector python3 -m ocr en