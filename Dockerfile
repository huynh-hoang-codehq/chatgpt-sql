# Dockerfile
FROM python:3.9.10-alpine3.14
WORKDIR /code
RUN pip install --upgrade pip
COPY ./requirement.txt /code/requirement.txt
EXPOSE 8000
RUN apk update
RUN apk add make automake gcc g++ subversion python3-dev
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /code/requirement.txt

COPY ./app /code/app
ENV FLASK_APP=app
CMD ["python","/code/app/app.py"]