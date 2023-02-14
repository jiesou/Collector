docker rm -f paddleocr
docker build --tag paddleocr .
docker run --name paddleocr -idt --mount 'type=volume,src=paddleocr,dst=/root/.paddleocr' paddleocr
docker exec -it paddleocr python3 -m ocr