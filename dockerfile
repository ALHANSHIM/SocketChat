FROM python:3.12
WORKDIR /socketchat
COPY . .
RUN pip install --no-cache-dir .

ENTRYPOINT ["schat"]