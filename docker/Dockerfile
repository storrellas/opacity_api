FROM python:3.9-buster

# Set the working directory to bind-mount where project files are
WORKDIR /repo

# Install dependencies
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install gunicorn

ADD . /repo/

# Run container
CMD gunicorn --access-logfile=- --bind 0.0.0.0:8080 --timeout 300 opacity_api.wsgi

