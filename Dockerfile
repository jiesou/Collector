FROM registry.baidubce.com/paddlepaddle/paddle:2.4.1

WORKDIR /root

COPY app/requirements.txt .
RUN python3 -m pip install -r requirements.txt

COPY app .

CMD ["redis-server", "/etc/redis/redis.conf"]
CMD ["gunicorn", "web:app", "-c", "./gunicorn.conf.py"]