from vulcan import Keystore, Account, InvalidTokenException
import os


async def authenticate(token: str = "", symbol: str = "", pin: str = "", device_name: str = '') \
        -> (Keystore, Account):
    keystore = await load_keystore(device_name)
    if keystore is None:
        return None

    account = await load_credentials(keystore, token, symbol, pin)
    if account is None:
        return None
    return keystore, account


async def load_keystore(device_name: str) -> Keystore:
    os.mkdir("../creds") if not os.path.exists("../creds") else None
    file_path = "../creds/keystore.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            keystore = Keystore.load(file)
            print("Keystore loaded")
    else:
        if device_name == "":
            return None
        keystore = await Keystore.create(device_model=device_name)
        with open(file_path, "w") as file:
            file.write(keystore.as_json)
        print("Keystore created")
    return keystore


async def load_credentials(keystore: Keystore, token: str, symbol: str, pin: str) -> Account:
    os.mkdir("../creds") if not os.path.exists("../creds") else None
    file_path = "../creds/account.json"

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            account = Account.load(file)
            print("Account loaded")
            return account
    else:
        if keystore is None:
            return None
        if keystore is None or token == '' or symbol == '' or pin == '':
            return None
        account = await Account.register(keystore, token, symbol, pin)
        with open(file_path, "w") as file:
            file.write(account.as_json)
        print("Account registered")
        return account
