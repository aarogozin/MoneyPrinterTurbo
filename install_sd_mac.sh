#!/usr/bin/env bash

# This script automates cloning and setting up AUTOMATIC1111 Stable Diffusion WebUI on macOS
set -e

echo "=== Stable Diffusion WebUI Installer for macOS ==="

# 1. Verify OS is macOS
OS_NAME=$(uname)
if [ "$OS_NAME" != "Darwin" ]; then
  echo "Error: This script is only designed for macOS (Apple Silicon M1/M2/M3 recommended)."
  exit 1
fi

# 2. Get current parent directory to install SD alongside moneyprinterturbo
MONEYPRINTER_DIR=$(pwd)
PARENT_DIR=$(dirname "$MONEYPRINTER_DIR")
SD_DIR="$PARENT_DIR/stable-diffusion-webui"

echo "Installing Stable Diffusion WebUI to: $SD_DIR"

# 3. Check dependencies (Homebrew, python, git, wget/curl)
if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is not installed. Please install git first."
  exit 1
fi

# 4. Clone A1111 repository if it doesn't exist
if [ ! -d "$SD_DIR" ]; then
  echo "Cloning AUTOMATIC1111/stable-diffusion-webui..."
  git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git "$SD_DIR"
else
  echo "AUTOMATIC1111 repository already cloned."
fi

# 5. Download Stable Diffusion 1.5 Model (if it doesn't exist)
MODEL_PATH="$SD_DIR/models/Stable-diffusion/v1-5-pruned-emaonly.safetensors"
if [ ! -f "$MODEL_PATH" ]; then
  echo "Downloading Stable Diffusion 1.5 model (approx. 4GB)..."
  mkdir -p "$(dirname "$MODEL_PATH")"
  
  # Download from runwayml
  curl -L -o "$MODEL_PATH" "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors"
  echo "Model downloaded successfully."
else
  echo "Stable Diffusion 1.5 model already exists."
fi

# 6. Create local startup runner with --api enabled
START_SCRIPT="$SD_DIR/start_sd.sh"
echo "Creating helper startup script: $START_SCRIPT"

cat << 'EOF' > "$START_SCRIPT"
#!/usr/bin/env bash
# Start AUTOMATIC1111 WebUI with API enabled for MoneyPrinterTurbo
cd "$(dirname "$0")"
./webui.sh --api
EOF

chmod +x "$START_SCRIPT"

echo "==========================================================="
echo "Installation complete!"
echo "To start Stable Diffusion WebUI, run:"
echo "  cd $SD_DIR && ./start_sd.sh"
echo "==========================================================="
