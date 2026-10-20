FROM python:3.12-slim
WORKDIR /app

COPY app.py seed_urology.py cms_ingest.py generate_sample_uploads.py ./
COPY static ./static
COPY src ./src
COPY sample_uploads ./sample_uploads

RUN python3 seed_urology.py

ENV PORT=8080
ENV UROCURA_PUBLIC_DEMO=1
EXPOSE 8080

CMD ["python3", "app.py"]
