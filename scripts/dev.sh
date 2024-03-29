docker rm -f collector-dev
docker build --tag collector-dev .
docker run --name collector-dev -idt --restart unless-stopped --volume ./app/:/root/ -p 3000:3000 --env-file ./.env collector-dev
