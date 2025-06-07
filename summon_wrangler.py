import subprocess
import os
import urllib.request
import time
import shutil
import tempfile
import webbrowser
import ctypes
import sys

first_run_message = """
It looks like this is the first time Wrangler has been run on your system!

For the first run you will need to close this window and re-run this program with 
administrator priviledges - right click summon_wrangler.exe and select "Run as Administrator".

WHY
Wrangler depends on Docker to execute tasks, 
so this program will need to:
- Check WSL2, install/update/activate as needed (allows Windows to run virtualized containers)
- Install Docker (Manages containers)



NOTE
Once the first run and setup is complete you will need to do 2 things:
1. Reboot your computer - this will allow WSL2 to fully activate (Docker needs WSL2)

2. Open Docker and accept the EULA - this program cannot do that for you even with admin privs.

    2.a. Docker will give you the option to sign in - this is up to you. It will add more functionality
         to Docker if you want it, but is not needed for Wrangler to work.

After the installation and first run Wrangler will no longer need 
Administrator Privilleges and you can simply run the program as normal after that. 


"""


DOCKER_DOWNLOAD_URL = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
INSTALLER_NAME = "DockerInstaller.exe"
DOCKER_PROCESS_NAME = "Docker Desktop.exe"


##### should only get called if Docker is not installed AND wrangler was not run as admin #######
def confirm_or_exit(title="First Run/Setup", message=first_run_message):
    result = ctypes.windll.user32.MessageBoxW(0, message, title, 1)
    if result != 1:  # 1 = OK, anything else = Cancel or closed
        sys.exit("User cancelled the operation.")
    else:
        sys.exit("Please re-run summon_wrangler.exe as Administrator (first run/setup only).")



def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
        

def enable_windows_feature(feature_name):
    try:
        subprocess.run(
            ["dism.exe", "/online", "/enable-feature", f"/featurename:{feature_name}", "/all", "/norestart"],
            check=True
        )
        print(f"{feature_name} enabled.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to enable {feature_name}: {e}")


def check_wsl_version():
    try:
        result = subprocess.run(["wsl", "--version"], capture_output=True, text=True)
        output = result.stdout + result.stderr
        if "WSL version" in output or "WSL 2" in output:
            print("WSL is installed.")
            return True
        else:
            return False
    except FileNotFoundError:
        return False
    

def install_wsl_kernel_update():
    url = "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".msi") as f:
        print("Downloading WSL2 kernel update...")
        urllib.request.urlretrieve(url, f.name)
        print("Installing WSL2 kernel update...")
        subprocess.run(["msiexec", "/i", f.name, "/quiet", "/norestart"], check=True)
        os.remove(f.name)
        print("WSL2 kernel updated.")


def check_and_enable_wsl2_stack():
    if not is_admin():
        print("You must run this script as Administrator.")
        sys.exit(1)

    print("🔍 Checking WSL status...")
    wsl_installed = check_wsl_version()

    print("Enabling Windows features for WSL2...")
    enable_windows_feature("Microsoft-Windows-Subsystem-Linux")
    enable_windows_feature("VirtualMachinePlatform")
    enable_windows_feature("Containers")
    enable_windows_feature("Microsoft-Hyper-V-All")

    if not wsl_installed:
        print("WSL not fully installed. You may need to run: wsl --install")
    else:
        install_wsl_kernel_update()

    print("Please reboot your system to apply changes.")




def is_docker_installed():
    try:
        subprocess.run(["docker", "--version"], capture_output=True, text=True, check=True)
        return True
    except FileNotFoundError:
        return False

def download_docker_installer(destination):
    print("Downloading Docker Desktop installer...")
    try:
        urllib.request.urlretrieve(DOCKER_DOWNLOAD_URL, destination)
        print(f"Downloaded to {destination}")
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def install_docker(installer_path):
    print("Installing Docker Desktop silently...")
    try:
        subprocess.run([installer_path, "install", "--quiet"], check=True)
        print("Docker installation launched.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Docker installation failed: {e}")
        return False

def is_docker_running():
    try:
        subprocess.run(["docker", "info"], capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def start_docker_daemon():
    print("Starting Docker Desktop...")
    try:
        #subprocess.run(["powershell", "-Command", f"Start-Process '{DOCKER_PROCESS_NAME}'"], check=True)
        subprocess.run(["C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to launch Docker Desktop: {e}")
        return False

    print("Waiting for Docker daemon to be available...")
    for _ in range(30):
        if is_docker_running():
            print("Docker daemon is now running.")
            return True
        time.sleep(2)

    print("Docker daemon did not start in time.")
    return False



def start_new_tube():
    webbrowser.open('http://localhost:8501')
    subprocess.run(
        [
        "docker", 
        "run",
        "-it",
        "-v",
        "/var/run/docker.sock:/var/run/docker.sock",
        #"--rm", 
        "-d", 
        "-p",""
        "8501:8501",
        "--name",
        #"new-tube-container", 
        "container-wrangler",
        "griff85/wrangler:version1", 
        "sh", 
        "-c",
        #"bash"
        "streamlit run /home/wrangler.py --server.port=8501"
        ], 
        capture_output=True, text=True, check=True
        )
    output = subprocess.run(["docker", "logs", "new-tube-container"], capture_output=True, text=True)
    print(output.stdout)
    
    # streamlit run player.py --server.port=8866


def main():
    if not is_docker_installed():
        print("Docker not found. Attempting to install...")
        if is_admin != True:
            ###### this will kill script if user clicks CANCEL or closes window - only proceed if click OK #####
            confirm_or_exit(title="First Run/Setup", message=first_run_message)

        check_and_enable_wsl2_stack()
            

        with tempfile.TemporaryDirectory() as tempdir:
            installer_path = os.path.join(tempdir, INSTALLER_NAME)
            if not download_docker_installer(installer_path):
                return
            if not install_docker(installer_path):
                return
            print("Waiting for installation to finish...")
            time.sleep(30)  # Give time for install to complete
    else:
        print("Docker is already installed.")

    if not is_docker_running():
        print("Docker daemon is not running.")
        if not start_docker_daemon():
            return
    
    running_containers = subprocess.run(
            ["docker", "ps", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            check=True
        )
    containers = running_containers.stdout.strip().split('\n')

    print(type(containers))
    for i in containers:
        print(type(i))
        if '"Names":"container-wrangler"' in i:
            print("Wrangler container already running")
    
        else:
            print("Docker daemon is running. Starting Wrangler container.")
            start_new_tube()

    

if __name__ == "__main__":
    main()
