{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 # Step 1: Start with an official Python base image.\
FROM python:3.11-slim\
\
# Step 2: Set an environment variable to prevent interactive prompts during installation.\
ENV DEBIAN_FRONTEND=noninteractive\
\
# Step 3: Install all system dependencies: Tesseract, Ghostscript, and language packs.\
# This is the most critical step. It's like running `apt-get` on a fresh Linux server.\
RUN apt-get update && apt-get install -y \\\
    tesseract-ocr \\\
    tesseract-ocr-eng \\\
    tesseract-ocr-tur \\\
    tesseract-ocr-deu \\\
    tesseract-ocr-fra \\\
    tesseract-ocr-spa \\\
    ghostscript \\\
    --no-install-recommends && \\\
    rm -rf /var/lib/apt/lists/*\
\
# Step 4: Set the working directory inside the container.\
WORKDIR /app\
\
# Step 5: Copy the Python requirements file into the container.\
COPY requirements.txt .\
\
# Step 6: Install the Python packages.\
RUN pip install --no-cache-dir -r requirements.txt\
\
# Step 7: Copy the rest of your application code into the container.\
COPY . .\
\
# Step 8: Expose the port the app will run on.\
EXPOSE 10000\
\
# Step 9: The command to run your application using the Gunicorn server.\
# This is what starts your app when the container launches.\
CMD ["gunicorn", "--workers", "1", "--worker-class", "gevent", "--bind", "0.0.0.0:10000", "app:app"]}