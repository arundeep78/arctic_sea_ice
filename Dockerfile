# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

# Creates a non-root user with an explicit UID and adds permission to access the /app folder

# install curl
RUN apt-get update; apt install -y curl

ENV VAR1=10

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt


# Set environment for Flask app
ENV FLASK_APP="webapp.py"
ENV FLASK_ENV="development"

EXPOSE 5000

WORKDIR /app
COPY . /app



# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
#CMD ["gunicorn", "--bind", "0.0.0.0:5000", "webapp:app"]


# Run flask directly without Gunicorn
CMD [ "flask", "run", "--host=0.0.0.0" ]