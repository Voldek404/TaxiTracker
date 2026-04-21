
# Use the official Python runtime image
FROM python:3.13

# Create the app directory
RUN mkdir /app

# Set the working directory inside the container
WORKDIR /app

# Set environment variables
# Prevents Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
#Prevents Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# Upgrade pip
RUN pip install --upgrade pip

# Copy the Django project  and install dependencies
COPY requirements.txt  /app/

# run this command to install all dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the Django project to the container
COPY . /app/

# Expose the Django port
EXPOSE 8000

# Run Django’s development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]