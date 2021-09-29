from dataclasses import dataclass


@dataclass
class User:
    email: str


USERS = {
    u.email: u for u in [User(email="bob@example.com"), User(email="doug@example.com")]
}
