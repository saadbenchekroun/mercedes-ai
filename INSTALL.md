# Installation Guide for Mercedes AI System

This guide provides detailed instructions for setting up the Mercedes AI system in both development and production environments.

## Prerequisites

### Hardware Requirements
- NVIDIA Drive AGX Orin SoC
- 4-mic array (Knowles SPH0645LM4H-B MEMS)
- Burmester 4D surround sound system
- 4G/5G modem
- CAN bus interface

### Software Requirements
- Python 3.8 or higher
- NVIDIA DRIVE SDK
- Mercedes-Benz MBUX Development Kit
- Git

## Development Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/mercedes-benz/mercedes-ai.git
cd mercedes-ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -r requirements.txt
```

4. Set up development environment variables:
```bash
# Create a .env file in the project root
echo "DEEPGRAM_API_KEY=your_dev_key" > .env
echo "OPENAI_API_KEY=your_dev_key" >> .env
echo "AZURE_SPEECH_KEY=your_dev_key" >> .env
```

5. Install NVIDIA DRIVE SDK:
```bash
# Follow NVIDIA's installation guide for DRIVE SDK
# https://developer.nvidia.com/drive/drive-sdk
```

6. Install MBUX Development Kit:
```bash
# Follow Mercedes-Benz's installation guide for MBUX SDK
# https://developer.mercedes-benz.com/mbux
```

## Production Environment Setup

1. Set up the vehicle's computing environment:
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3.8 python3.8-venv python3.8-dev
```

2. Clone the repository:
```bash
git clone https://github.com/saadbenchekroun/mercedes-ai.git
cd mercedes-ai
```

3. Create and activate a virtual environment:
```bash
python3.8 -m venv venv
source venv/bin/activate
```

4. Install production dependencies:
```bash
pip install -r requirements.txt
```

5. Set up production environment variables:
```bash
# Set environment variables in the system
sudo nano /etc/environment
# Add the following lines:
DEEPGRAM_API_KEY=your_prod_key
OPENAI_API_KEY=your_prod_key
AZURE_SPEECH_KEY=your_prod_key
```

6. Configure the system service:
```bash
# Create a systemd service file
sudo nano /etc/systemd/system/mercedes-ai.service

# Add the following content:
[Unit]
Description=Mercedes AI System
After=network.target

[Service]
Type=simple
User=mercedes-ai
WorkingDirectory=/opt/mercedes-ai
Environment=PYTHONPATH=/opt/mercedes-ai
ExecStart=/opt/mercedes-ai/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

7. Start the service:
```bash
sudo systemctl enable mercedes-ai
sudo systemctl start mercedes-ai
```

## Hardware Setup

1. Connect the 4-mic array:
```bash
# Verify microphone connections
arecord -l
```

2. Configure the CAN bus interface:
```bash
# Set up CAN interface
sudo ip link set can0 type can bitrate 500000
sudo ip link set up can0
```

3. Configure the sound system:
```bash
# Test audio output
aplay -l
```

## Verification

1. Check the system status:
```bash
sudo systemctl status mercedes-ai
```

2. View the logs:
```bash
tail -f /var/log/mercedes-ai/mercedes_ai.log
```

3. Run the test suite:
```bash
pytest tests/
```

## Troubleshooting

### Common Issues

1. Microphone not detected:
```bash
# Check microphone permissions
sudo usermod -a -G audio $USER
```

2. CAN bus errors:
```bash
# Check CAN interface status
ip link show can0
```

3. Audio output issues:
```bash
# Check audio device configuration
alsamixer
```

### Getting Help

For additional support:
- Check the [documentation](docs/)
- Contact the Mercedes-Benz AI Systems Team at ai-systems@mercedes-benz.com
- Submit an issue on the [GitHub repository](https://github.com/mercedes-benz/mercedes-ai/issues)

## Security Considerations

1. API Keys:
- Never commit API keys to version control
- Rotate keys regularly
- Use environment variables for sensitive data

2. System Security:
- Keep the system updated
- Monitor system logs
- Follow security best practices

## Maintenance

1. Regular Updates:
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade
```

2. Log Rotation:
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/mercedes-ai
```

3. Backup:
```bash
# Backup configuration and data
sudo tar -czf mercedes-ai-backup.tar.gz /opt/mercedes-ai
``` 
