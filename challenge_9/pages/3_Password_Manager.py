import streamlit as st
from pathlib import Path
import json
import pandas as pd
from cryptography.fernet import Fernet

st.set_page_config(
    page_title="Password Manager",
)

if st.button("Load from plaintext"):
    if Path("passwords.txt").exists():
        with open("passwords.txt", "r") as file:
            st.table(pd.array(file.readlines()))
    else:
        st.warning("Could not find passwords.txt!")

if st.button("Load from encrypted database"):
    if Path("passwords.jsonl").exists():
        if Path("secret.key").exists():
            with open("secret.key", "b+r") as b:
                key = b.read()
                cipher = Fernet(key)


            with open("passwords.jsonl", "r", encoding="utf-8") as file:
                all_passes = [json.loads(line)["password"] for line in file if json.loads(line)["type"] == "insert"]
                d = [cipher.decrypt(p).decode("utf-8") for p in all_passes]
                st.table(pd.array(d))

        else:
            st.warning("Could not find secret.key!")
    
    else:
        st.warning("Could not find passwords.jsonl!")