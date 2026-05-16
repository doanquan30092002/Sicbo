from abc import ABC, abstractmethod


class INotificationPort(ABC):
    @abstractmethod
    async def send_user_message(self, telegram_id: int, text: str) -> bool:
        """Gửi tin nhắn cho user qua Telegram. Returns False nếu user chưa link Telegram."""
        ...

    @abstractmethod
    async def send_admin_message(self, text: str) -> None:
        """Gửi tin nhắn cho admin group/chat."""
        ...
