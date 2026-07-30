import streamlit as st
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
import secrets
import string
import json

KEY_FILE = Path("secret.key")

def generate_password(length, include_numbers=True, include_special=True):
    chars = string.ascii_letters
    
    if include_numbers:
        chars += string.digits
    if include_special:
        chars += string.punctuation

    password = ''.join(secrets.choice(chars) for _ in range(length))
    return password

st.set_page_config(
    page_title="Password Generator",
)

st.write("# Password Generator")

if "password" not in st.session_state:
    st.session_state.password = None

length = st.slider("Length", 4, 20, 12)
allow_spec = st.checkbox("Special Characters?")
allow_num = st.checkbox("Numbers?")

if st.button("Generate"):
    st.session_state.password = generate_password(
        length,
        include_numbers=allow_num,
        include_special=allow_spec,
    )

if st.session_state.password is not None:
    st.code(st.session_state.password, language="text")

    export_format = st.selectbox(
        "Export format",
        ["PLAINTEXT", "AES-128 ENCRYPTED"],
    )

    if export_format == "PLAINTEXT":
        if st.button("Save to file"):
            if Path("passwords.txt").exists():
                with open("passwords.txt", "r") as file:
                    all_passes = [p.strip() for p in file.readlines()]
            else:
                with open("passwords.txt", "x") as file:
                    file.write("")
                
                all_passes = []

            if st.session_state.password not in all_passes:
                with open("passwords.txt", "a") as file:
                    file.write(st.session_state.password + "\n")
                st.success("Saved to passwords.txt")
            else:
                st.warning("Already added this password!")

    elif export_format == "AES-128 ENCRYPTED":
        if not KEY_FILE.exists():
            st.warning("Key file not found")

            if st.button("Make new key file"):
                key = Fernet.generate_key()
                KEY_FILE.write_bytes(key)
                st.success("Key file created")
                st.rerun()

            st.stop()

        key = KEY_FILE.read_bytes()
        cipher = Fernet(key)

        if st.button("Save to file"):
            encrypted_password = cipher.encrypt(
                st.session_state.password.encode("utf-8")
            ).decode("utf-8")

            digest = hashes.Hash(hashes.SHA256())

            digest.update(st.session_state.password.encode("utf-8"))

            raw_bytes = digest.finalize()

            h = raw_bytes.hex()

            data = {"type": "insert", "hash": h, "password": encrypted_password}

            if Path("passwords.jsonl").exists():
                with open("passwords.jsonl", "r", encoding="utf-8") as file:
                    all_hashes = [json.loads(line)["hash"] for line in file]
            else:
                with open("passwords.jsonl", "x") as file:
                    file.write("")

                all_hashes = []

            if h not in all_hashes:
                with open("passwords.jsonl", "a") as file:
                    file.write(json.dumps(data) + "\n")
                    st.success("Saved to passwords.jsonl")
            else:
                st.warning("Already added this password!")