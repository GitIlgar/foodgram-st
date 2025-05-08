FROM python:3.13.2-alpine

WORKDIR /backend

COPY . .

RUN pip install -r requirements.txt

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]
