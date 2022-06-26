from typing import TYPE_CHECKING

from .types import URL, Email, Phone

if TYPE_CHECKING:
    from typing import Optional

BANNER_URL = "https://cdn.discordapp.com/banners/{}/{}"
AVATAR_URL = "https://cdn.discordapp.com/avatars/{}/{}"


class User:
    def __init__(self, data: dict):
        self.id: int = int(data.get("id"))
        self.bot: bool = data.get("bot", False)
        self.system: bool = data.get("system", False)

        self.username: str = data.get("username")
        self.discriminator: str = data.get("discriminator")

        self.flags: int = data.get("flags")
        self.public_flags: int = data.get("public_flags")

        self.banner: Optional[URL] = (
            URL(BANNER_URL.format(self.id, banner)) if (banner := data.get("banner")) else None
        )
        self.banner_color: Optional[str] = data.get("banner_color")
        self.avatar: URL = URL(AVATAR_URL.format(self.id, data.get("avatar")))
        self.avatar_decoration: bool = data.get("avatar_decoration", False)

        self.premium_type: int = data.get("premium_type")


class ClientUser(User):
    def __init__(self, data: dict):
        super().__init__(data)
        self.locale: str = data.get("locale")
        self.verified: bool = data.get("verified", False)

        self.email: Optional[Email] = Email(_email) if (_email := data.get("email")) else None
        self.phone: Optional[Phone] = Phone(_phone) if (_phone := data.get("phone")) else None
        self.mfa_enabled: bool = data.get("mfa_enabled", False)
