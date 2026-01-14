#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
VM_NAME="browsergym-agent"
ZONE="us-central1-a"
MACHINE_TYPE="n1-standard-8"
BOOT_DISK_SIZE="100GB"

echo "==========================================="
echo "BrowserGym GCP Deployment Script"
echo "==========================================="
echo "Project: $PROJECT_ID"
echo "VM Name: $VM_NAME"
echo "Zone: $ZONE"
echo "Machine Type: $MACHINE_TYPE"
echo "==========================================="
echo ""

# Step 1: Enable required APIs
echo "Step 1: Enabling required APIs..."
gcloud services enable compute.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
echo "✓ APIs enabled"
echo ""

# Step 2: Create service account for the VM
echo "Step 2: Creating service account..."
SA_NAME="browsergym-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account exists
if gcloud iam service-accounts describe $SA_EMAIL --project=$PROJECT_ID &>/dev/null; then
    echo "Service account already exists: $SA_EMAIL"
else
    gcloud iam service-accounts create $SA_NAME \
        --display-name="BrowserGym Service Account" \
        --project=$PROJECT_ID
    echo "✓ Service account created: $SA_EMAIL"
fi

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/aiplatform.user" \
    --condition=None

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/logging.logWriter" \
    --condition=None

echo "✓ Permissions granted"
echo ""

# Step 3: Create startup script
echo "Step 3: Creating startup script..."
cat > /tmp/startup-script.sh << 'STARTUP_EOF'
#!/bin/bash
set -e

# Log everything
exec > >(tee -a /var/log/browsergym-setup.log)
exec 2>&1

echo "=== BrowserGym Setup Started: $(date) ==="

# Wait for apt locks to be released
while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 ; do
    echo "Waiting for other apt processes to finish..."
    sleep 5
done

# Update system
echo "Updating system packages..."
sudo apt-get update
export DEBIAN_FRONTEND=noninteractive
sudo apt-get upgrade -y

# Install Python 3.11
echo "Installing Python 3.11..."
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install system dependencies for Chromium
echo "Installing Chromium dependencies..."
sudo apt-get install -y \
    wget gnupg ca-certificates fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 \
    libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 \
    libgbm1 libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 \
    libnss3 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 \
    libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 \
    libxrender1 libxss1 libxtst6 lsb-release xdg-utils \
    xvfb git build-essential curl vim tmux htop

# Get the primary user
BROWSERGYM_USER=$(ls /home | head -n 1)
BROWSERGYM_HOME="/home/$BROWSERGYM_USER"

echo "Setting up environment for user: $BROWSERGYM_USER"

# Switch to user context for remaining setup
sudo -u $BROWSERGYM_USER bash << 'USER_SETUP_EOF'
set -e

cd ~

# Create virtual environment
echo "Creating Python virtual environment..."
python3.11 -m venv ~/browsergym-env

# Activate and install packages
source ~/browsergym-env/bin/activate

echo "Installing Python packages..."
pip install --upgrade pip setuptools wheel

# Install BrowserGym packages
pip install browsergym agentlab

# Install Google GenAI SDK (the new, unified package)
pip install google-genai

# Install Playwright
echo "Installing Playwright and Chromium..."
pip install playwright
playwright install chromium
playwright install-deps chromium

# Set up Xvfb
echo "Setting up virtual display..."
cat > ~/start_xvfb.sh << 'XVFB_EOF'
#!/bin/bash
# Kill existing Xvfb if running
pkill Xvfb 2>/dev/null || true
# Start new Xvfb
Xvfb :99 -screen 0 1280x720x24 > /dev/null 2>&1 &
sleep 2
export DISPLAY=:99
XVFB_EOF

chmod +x ~/start_xvfb.sh
~/start_xvfb.sh

# Create environment configuration
echo "Creating environment configuration..."
mkdir -p ~/.config/browsergym

cat > ~/.config/browsergym/env.sh << 'ENV_EOF'
#!/bin/bash

# Google Cloud Configuration
export GOOGLE_CLOUD_PROJECT="$(gcloud config get-value project 2>/dev/null)"
export GOOGLE_CLOUD_REGION="us-central1"

# AgentLab Configuration
export AGENTLAB_EXP_ROOT="$HOME/agentlab_results"

# Vertex AI Configuration (for Gemini via google-genai)
export VERTEX_AI_PROJECT="$GOOGLE_CLOUD_PROJECT"
export VERTEX_AI_LOCATION="us-central1"

# Display for headless browser
export DISPLAY=:99

# Activate virtual environment
source $HOME/browsergym-env/bin/activate
ENV_EOF

chmod +x ~/.config/browsergym/env.sh

# Add to .bashrc
if ! grep -q "browsergym/env.sh" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# BrowserGym environment" >> ~/.bashrc
    echo "source ~/.config/browsergym/env.sh" >> ~/.bashrc
    echo "~/start_xvfb.sh 2>/dev/null || true" >> ~/.bashrc
fi

# Create Gemini integration directory
echo "Creating Gemini integration..."
mkdir -p ~/browsergym-gemini
cd ~/browsergym-gemini

# Create gemini_llm.py using google-genai package
cat > gemini_llm.py << 'GEMINI_LLM_EOF'
"""
Gemini LLM integration for BrowserGym using google-genai package
https://github.com/googleapis/python-genai
"""
import os
from typing import List, Dict, Any, Optional
from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch


class GeminiLLM:
    """Wrapper for Gemini using google-genai package"""
    
    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        project_id: Optional[str] = None,
        location: str = "us-central1",
        temperature: float = 0.0,
        max_output_tokens: int = 8192,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        
        # Get project ID
        project_id = (
            project_id or 
            os.environ.get("VERTEX_AI_PROJECT") or 
            os.environ.get("GOOGLE_CLOUD_PROJECT")
        )
        if not project_id:
            raise ValueError("project_id must be provided or set in environment")
        
        # Initialize client with Vertex AI
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        
        # Configure generation
        self.config = GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        
        self.chat = None
    
    def start_chat(self):
        """Start a new chat session"""
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=self.config,
        )
    
    def send_message(self, message: str, image_data: Optional[bytes] = None) -> str:
        """
        Send message to Gemini
        
        Args:
            message: Text message
            image_data: Optional image bytes for vision
            
        Returns:
            Response text
        """
        if self.chat is None:
            self.start_chat()
        
        # Prepare content
        if image_data:
            # For multimodal input with image
            parts = [
                {"text": message},
                {"inline_data": {"mime_type": "image/png", "data": image_data}}
            ]
            response = self.chat.send_message(parts)
        else:
            # Text only
            response = self.chat.send_message(message)
        
        return response.text
    
    def generate_content(self, prompt: str, image_data: Optional[bytes] = None) -> str:
        """
        Generate content without chat history (stateless)
        
        Args:
            prompt: Text prompt
            image_data: Optional image bytes
            
        Returns:
            Response text
        """
        if image_data:
            parts = [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/png", "data": image_data}}
            ]
        else:
            parts = prompt
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=parts,
            config=self.config,
        )
        
        return response.text


class GeminiAgent:
    """BrowserGym agent using Gemini"""
    
    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        use_screenshot: bool = False,
        temperature: float = 0.0,
    ):
        self.llm = GeminiLLM(
            model_name=model_name,
            temperature=temperature,
        )
        self.use_screenshot = use_screenshot
        self.action_history = []
        self.llm.start_chat()
    
    def get_action(self, obs: Dict[str, Any]) -> str:
        """
        Get next action from Gemini based on observation
        
        Args:
            obs: BrowserGym observation dictionary
            
        Returns:
            Action string
        """
        # Build prompt
        prompt = self._build_prompt(obs)
        
        # Get screenshot if enabled
        image_data = None
        if self.use_screenshot and "screenshot" in obs:
            # BrowserGym provides PIL Image, convert to bytes
            import io
            img = obs["screenshot"]
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            image_data = img_byte_arr.getvalue()
        
        # Get response from Gemini
        response = self.llm.send_message(prompt, image_data=image_data)
        
        # Extract action from response
        action = self._extract_action(response)
        
        # Store in history
        self.action_history.append({
            "observation": obs.get("url", ""),
            "response": response,
            "action": action
        })
        
        return action
    
    def _build_prompt(self, obs: Dict[str, Any]) -> str:
        """Build prompt from observation"""
        prompt_parts = []
        
        # Add goal
        if "goal" in obs:
            prompt_parts.append(f"Goal: {obs['goal']}")
        
        # Add current page info
        if "url" in obs:
            prompt_parts.append(f"Current URL: {obs['url']}")
        
        # Add accessible tree (simplified DOM)
        if "axtree_txt" in obs:
            # Truncate if too long
            axtree = obs['axtree_txt']
            if len(axtree) > 10000:
                axtree = axtree[:10000] + "...[truncated]"
            prompt_parts.append(f"Page content:\n{axtree}")
        
        # Add instruction
        prompt_parts.append(
            "\nProvide the next action to take. "
            "Use BrowserGym action format. Examples:\n"
            "- click('element_id')\n"
            "- fill('input_id', 'text to type')\n"
            "- goto('https://example.com')\n"
            "- scroll('down')\n"
            "- noop()  # for no action\n\n"
            "Return ONLY the action, no explanation."
        )
        
        return "\n\n".join(prompt_parts)
    
    def _extract_action(self, response: str) -> str:
        """Extract action from Gemini response"""
        # Clean up response
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
        
        # Take first non-comment line
        for line in response.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("//"):
                return line
        
        return "noop()"  # Fallback


if __name__ == "__main__":
    # Quick test
    print("Testing GeminiLLM...")
    llm = GeminiLLM()
    response = llm.generate_content("Say 'Hello from google-genai package!'")
    print(f"Response: {response}")
    print("✓ GeminiLLM working!")
GEMINI_LLM_EOF

echo "✓ gemini_llm.py created"

# Create test script
cat > test_gemini.py << 'TEST_EOF'
#!/usr/bin/env python3
"""Test Gemini integration using google-genai"""
import os
from gemini_llm import GeminiLLM

print("=" * 50)
print("Testing Gemini connection via google-genai")
print("=" * 50)
print(f"Project: {os.environ.get('VERTEX_AI_PROJECT')}")
print(f"Location: {os.environ.get('VERTEX_AI_LOCATION')}")
print()

try:
    llm = GeminiLLM(model_name="gemini-2.0-flash-exp")
    
    # Test 1: Simple generation
    print("Test 1: Simple text generation")
    response = llm.generate_content("Say 'Hello from BrowserGym on GCP with google-genai!'")
    print(f"✓ Response: {response}")
    print()
    
    # Test 2: Chat session
    print("Test 2: Chat session")
    llm.start_chat()
    response1 = llm.send_message("What is 2+2?")
    print(f"✓ Q1: {response1}")
    response2 = llm.send_message("What about 3+3?")
    print(f"✓ Q2: {response2}")
    print()
    
    print("=" * 50)
    print("✓ All tests passed! Gemini is working!")
    print("=" * 50)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
TEST_EOF

chmod +x test_gemini.py

# Create demo BrowserGym script
cat > demo_browsergym.py << 'DEMO_EOF'
#!/usr/bin/env python3
"""Simple BrowserGym demo with Chromium"""
import gymnasium as gym
import browsergym.core

print("=" * 50)
print("Testing BrowserGym with Chromium")
print("=" * 50)

try:
    print("Creating environment...")
    env = gym.make(
        "browsergym/openended",
        task_kwargs={"start_url": "https://www.google.com/"},
    )
    
    print("Resetting environment...")
    obs, info = env.reset()
    
    print("✓ Environment initialized successfully!")
    print(f"✓ Current URL: {obs.get('url', 'N/A')}")
    
    # Take a simple action
    print("Taking test action...")
    obs, reward, terminated, truncated, info = env.step("noop()")
    
    print("✓ Action executed successfully!")
    print()
    print("=" * 50)
    print("✓ BrowserGym is working!")
    print("=" * 50)
    
    env.close()
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
DEMO_EOF

chmod +x demo_browsergym.py

# Create full agent demo
cat > run_gemini_agent.py << 'AGENT_EOF'
#!/usr/bin/env python3
"""
Run BrowserGym agent with Gemini
"""
import gymnasium as gym
import browsergym.core
from gemini_llm import GeminiAgent


def main():
    print("=" * 60)
    print("BrowserGym Agent with Gemini (google-genai)")
    print("=" * 60)
    print()
    
    # Create environment
    print("Creating environment...")
    env = gym.make(
        "browsergym/openended",
        task_kwargs={"start_url": "https://www.google.com/"},
    )
    
    # Create Gemini agent
    print("Creating Gemini agent...")
    agent = GeminiAgent(
        model_name="gemini-2.0-flash-exp",
        use_screenshot=False,  # Set to True to use vision
        temperature=0.0,
    )
    
    print("Starting episode...")
    print()
    
    # Run episode
    obs, info = env.reset()
    print(f"Goal: {obs.get('goal', 'Interactive exploration')}")
    print(f"Starting URL: {obs.get('url')}")
    print()
    
    max_steps = 10
    for step in range(max_steps):
        print(f"--- Step {step + 1}/{max_steps} ---")
        
        # Get action from agent
        action = agent.get_action(obs)
        print(f"Action: {action}")
        
        # Execute action
        try:
            obs, reward, terminated, truncated, info = env.step(action)
            print(f"Reward: {reward}")
            
            if terminated or truncated:
                print(f"\n✓ Episode finished!")
                print(f"Final reward: {reward}")
                break
        except Exception as e:
            print(f"Action failed: {e}")
            break
        
        print()
    
    env.close()
    print()
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
AGENT_EOF

chmod +x run_gemini_agent.py

# Create README
cat > README.md << 'README_EOF'
# BrowserGym with Gemini on GCP

This setup uses the `google-genai` package for Gemini integration with BrowserGym.

## Quick Start

```bash
# Test Gemini connection
python3 test_gemini.py

# Test BrowserGym
python3 demo_browsergym.py

# Run full agent demo
python3 run_gemini_agent.py
