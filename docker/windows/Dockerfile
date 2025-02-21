# Use a Windows-based Python image
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . .

# Install Python
RUN powershell -Command `
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe" -OutFile "python.exe"; `
Start-Process -FilePath "python.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -NoNewWindow -Wait; `
Remove-Item -Force "python.exe"

# Install dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt
RUN python -m pip install --no-cache-dir -r requirements_dev.txt

# Build the Windows executable
RUN python -m PyInstaller --onefile --name four-souls-mpc-formatter main.py

# Define output directory
VOLUME ["C:/output"]

# Move the built EXE to the output directory
RUN powershell Move-Item -Path C:/app/dist/four-souls-mpc-formatter.exe -Destination C:/output/

CMD ["cmd", "/c", "echo Build complete! Check the C:/output directory."]
