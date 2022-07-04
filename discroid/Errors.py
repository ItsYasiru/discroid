class DiscroidError(Exception):
    pass


class HTTPError(DiscroidError):
    pass


class WebsocketError(DiscroidError):
    pass


class LoginFailure(HTTPError):
    pass


class SocketClosure(WebsocketError):
    pass
