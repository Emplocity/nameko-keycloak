from typing import Any, Callable, Dict, Optional

# do not assume anything about a User type
User = Any
Token = str
TokenPayload = Dict[str, Any]
FetchUserCallable = Callable[[str], Optional[User]]
