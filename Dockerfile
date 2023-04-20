# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY bot.py .

# Set the environment variables
ENV TELEGRAM_BOT_TOKEN your_bot_token
ENV OPENAI_API_KEY your_openai_api_key

# Run the Python script when the container starts
CMD ["python", "bot.py"]
