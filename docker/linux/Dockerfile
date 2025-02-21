# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install necessary system dependencies for PyInstaller
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    musl-dev \
    patchelf \
    && rm -rf /var/lib/apt/lists/*

# Copy the project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements_dev.txt

# Build the executable
RUN pyinstaller --onefile --name four-souls-mpc-formatter main.py
# RUN pyinstaller --onefile --name four-souls-mpc-formatter --distpath /app/dist main.py

# Ensure /output directory exists
RUN mkdir -p /output

# Debugging: Print the contents of /app/dist before moving
RUN ls -l /app/dist

# Move the built executable to the mounted output directory
# RUN mv /app/dist/* /output/
RUN cp /app/dist/* /output/

# Debugging: Print the contents of /output to confirm the move
RUN ls -l /output

# Set the default command
CMD ["echo", "Build complete! Check the /output directory."]
