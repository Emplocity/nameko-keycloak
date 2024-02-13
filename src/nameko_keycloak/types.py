from typing import Any, Callable, Optional

# do not assume anything about a User type
User = Any
Token = str
TokenPayload = dict[str, Any]
FetchUserCallable = Callable[[str, TokenPayload], Optional[User]]
