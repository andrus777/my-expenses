from app.auth.passwords import hash_password, verify_password


def test_password_is_hashed_and_can_be_verified():
    password = "correct horse battery staple"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password not in password_hash
    assert verify_password(password_hash, password)
    assert not verify_password(password_hash, "wrong password")
