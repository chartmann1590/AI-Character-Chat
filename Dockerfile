# Start from a small Python base image
FROM python:3.9-slim-buster

# These environment variables prevent Python from writing out pyc files and buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create the working directory inside the container
WORKDIR /usr/src/app

# Copy only requirements first, to leverage Docker's caching for dependency installation
COPY requirements.txt /usr/src/app/

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container (excluding things listed in .dockerignore)
COPY . /usr/src/app/

# Expose the port your app runs on. Adjust if needed.
EXPOSE 5000

# By default, run your application
CMD ["python", "app.py"]
