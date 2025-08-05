import bcrypt


def hash_pwd(pwd: str) -> str:
    hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt())
    return str(hashed.decode())


def check_pwd(pwd: str, hashed: str) -> bool:
    result = bcrypt.checkpw(pwd.encode(), hashed.encode())
    return bool(result)
