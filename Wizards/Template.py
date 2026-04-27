import os
import winreg
import requests
from win32com.client import Dispatch

# Downloads an exe to AppData, then creates a Desktop shortcut — reads Desktop path from registry to support all languages

file_url = "https://Placeholder.com"
filename = "FileNameTest.exe"

appdata_roaming = os.getenv('APPDATA')
destination_folder = os.path.join(appdata_roaming, "InstallWizardTest67")

if not os.path.exists(destination_folder):
    os.makedirs(destination_folder)

file_path = os.path.join(destination_folder, filename)

def get_desktop_path():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
    desktop, _ = winreg.QueryValueEx(key, "Desktop")
    return desktop

print(f"Downloading {filename} to AppData...")
try:
    response = requests.get(file_url, stream=True)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download Finished!")

        desktop = get_desktop_path()
        print(f"Desktop found at: {desktop}")
        shortcut_path = os.path.join(desktop, "InstallWizardTest.lnk")

        print(f"Creating Shortcut at: {shortcut_path}")
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = file_path
        shortcut.WorkingDirectory = destination_folder
        if filename.endswith(('.exe', '.ico')):
            shortcut.IconLocation = file_path
        shortcut.save()

        print(f"Success! Shortcut created on Desktop.")
    else:
        print(f"Error: Website returned status {response.status_code}. Check your URL!")
except Exception as e:
    print(f"An error occurred: {e}")

input("\nInstallation Complete! Press Enter to exit...")