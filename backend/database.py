
import os
import tempfile

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

db_ssl_ca = os.getenv("DB_SSL_CA")

if db_ssl_ca and "-----BEGIN CERTIFICATE-----" in db_ssl_ca:
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".pem",
        delete=False,
        encoding="utf-8"
    ) as ca_file:
        ca_file.write(db_ssl_ca.strip() + "\n")
        db_ssl_ca = ca_file.name


def get_connection():
    connection_config = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
    }

    if db_ssl_ca:
        connection_config["ssl_ca"] = db_ssl_ca
        connection_config["ssl_verify_cert"] = True

    connection = mysql.connector.connect(**connection_config)

    return connection
