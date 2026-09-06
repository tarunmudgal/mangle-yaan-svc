# Environment Setup

This document provides step-by-step instructions for setting up the **MangleYaan** framework on your local machine.

## Prerequisites
- **Python**: 3.7+ is recommended.
- **Git**: To clone the repository.
- **Kubectl**: Configured to connect to your target test clusters (Optional, depends on how the test environments are provisioned).

---

## MacOS Setup

1. **Install Homebrew (if not installed):**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python 3:**
   ```bash
   brew install python
   ```

3. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd mangle-yaan-service
   ```

4. **Create a Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install Dependencies:**
   Ensure you are using `pip` to install dependencies from any provided `requirements.txt` or standard setup files, if they exist:
   ```bash
   pip install -r requirements.txt
   # OR if using setup.py/tox
   pip install tox
   ```

---

## Windows Setup

1. **Install Chocolatey (if not installed):**
   Open PowerShell as Administrator and run:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. **Install Python 3:**
   ```powershell
   choco install python -y
   ```

3. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd mangle-yaan-service
   ```

4. **Create a Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   *(Note: You might need to set execution policies to run scripts via `Set-ExecutionPolicy Unrestricted -Scope CurrentUser`)*

5. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

---

## Configuration

Before running tests, ensure that you have your environment variables and standard configuration files set up.
- **Config File:** `my.json` (Needs to be provided and placed in the appropriate `config/` directory based on your specific cluster endpoints).
- **Kubeconfig:** Ensure your `.kube/config` is pointed to the target cluster if performing k8s operations locally.
