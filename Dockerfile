FROM ghcr.io/anime-republic/wzml:latest
RUN pip install git+https://github.com/KurimuzonAkuma/pyrogram.git
COPY . .
CMD ["bash", "start.sh"]
