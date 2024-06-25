
FROM balapriyanb/neonspectre:latest

WORKDIR /usr/src/app

RUN mkdir -p /usr/src/app && chmod 777 /usr/src/app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash", "start.sh"]
