FROM balapriyanb/neonspectre:latest

WORKDIR /usr/src/app
COPY . .

RUN chmod +x start.sh

CMD ["bash", "./start.sh"]
