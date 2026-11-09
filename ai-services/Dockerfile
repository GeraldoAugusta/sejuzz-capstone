FROM python:3.12-slim AS pick
COPY . /src
RUN mkdir /pick \
 && if [ -d /src/ai-services/app ]; then B=/src/ai-services; else B=/src; fi \
 && cp "$B/requirements.txt" /pick/ \
 && cp -r "$B/app" /pick/app

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=pick /pick/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=pick /pick/app ./app
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
