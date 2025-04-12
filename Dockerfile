# Start from a small Python base image
FROM python:3.9-slim-buster

# Prevent Python from writing pyc files and buffering output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app into the container
COPY . /usr/src/app/

# Expose the port Flask uses
EXPOSE 5000

# Set Flask environment variable
ENV FLASK_APP=app.py

# Initialize and apply migrations at startup
CMD flask db upgrade && python app.py
