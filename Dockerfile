# Step 1: Start with an official Python base image.
FROM python:3.11-slim

# Step 2: Set an environment variable to prevent interactive prompts during installation.
ENV DEBIAN_FRONTEND=noninteractive

# Step 3: Install all system dependencies: Tesseract, Ghostscript, and language packs.
# This is the most critical step. It's like running `apt-get` on a fresh Linux server.
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-tur \
    tesseract-ocr-deu \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    ghostscript \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Step 4: Set the working directory inside the container.
WORKDIR /app

# Step 5: Copy the Python requirements file into the container.
COPY requirements.txt .

# Step 6: Install the Python packages.
RUN pip install --no-cache-dir -r requirements.txt

# Step 7: Copy the rest of your application code into the container.
COPY . .

# Step 8: Expose the port the app will run on.
EXPOSE 10000

# Step 9: The command to run your application using the Gunicorn server.
# This is what starts your app when the container launches.
# The final command to run our startup script.
CMD ["./startup.sh"]