import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select

from app.bot import bot
from app.db.notification import Notification, NotificationStatus, NotificationType
from app.db.session import AsyncSessionLocal
from app.db.task import Task
from app.db.user import User


class NotificationService:
    """Сервис для управления уведомлениями"""

    @staticmethod
    async def create_notification(
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Создает новое уведомление"""
        async with AsyncSessionLocal() as session:
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                scheduled_at=scheduled_at,
                metadata=json.dumps(metadata) if metadata else None,
            )
            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            return notification

    @staticmethod
    async def send_notification(notification_id: int) -> bool:
        """Отправляет уведомление пользователю"""
        async with AsyncSessionLocal() as session:
            # Получаем уведомление
            result = await session.execute(
                select(Notification).where(Notification.id == notification_id)
            )
            notification = result.scalar_one_or_none()

            if not notification:
                return False

            # Получаем пользователя
            result = await session.execute(
                select(User).where(User.id == notification.user_id)
            )
            user = result.scalar_one_or_none()

            if not user or not user.notifications_enabled:
                return False

            try:
                # Отправляем сообщение в Telegram
                await bot.send_message(
                    chat_id=user.tg_id,
                    text=f"🔔 **{notification.title}**\n\n{notification.message}",
                    parse_mode="Markdown",
                )

                # Обновляем статус
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now()
                await session.commit()

                return True

            except Exception:
                notification.status = NotificationStatus.FAILED
                await session.commit()
                return False

    @staticmethod
    async def mark_as_read(notification_id: int) -> bool:
        """Отмечает уведомление как прочитанное"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Notification).where(Notification.id == notification_id)
            )
            notification = result.scalar_one_or_none()

            if not notification:
                return False

            notification.status = NotificationStatus.READ
            notification.read_at = datetime.now()
            await session.commit()
            return True

    @staticmethod
    async def get_user_notifications(
        user_id: int, limit: int = 10, unread_only: bool = False
    ) -> List[Notification]:
        """Получает уведомления пользователя"""
        async with AsyncSessionLocal() as session:
            query = select(Notification).where(Notification.user_id == user_id)

            if unread_only:
                query = query.where(Notification.status == NotificationStatus.SENT)

            query = query.order_by(Notification.created_at.desc()).limit(limit)

            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def create_task_reminder(
        task_id: int, user_id: int, hours_before: int = 24
    ) -> Notification:
        """Создает напоминание о задаче"""
        async with AsyncSessionLocal() as session:
            # Получаем задачу
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalar_one_or_none()

            if not task or not task.deadline:
                raise ValueError("Задача не найдена или не имеет дедлайна")

            scheduled_at = task.deadline - timedelta(hours=hours_before)

            return await NotificationService.create_notification(
                user_id=user_id,
                notification_type=NotificationType.TASK_REMINDER,
                title="⏰ Напоминание о задаче",
                message=f"Задача '{task.title}' должна быть выполнена через {hours_before} часов",
                scheduled_at=scheduled_at,
                metadata={"task_id": task_id, "hours_before": hours_before},
            )

    @staticmethod
    async def create_broadcast_notification(
        user_ids: List[int], title: str, message: str
    ) -> List[Notification]:
        """Создает массовое уведомление"""
        notifications = []
        for user_id in user_ids:
            notification = await NotificationService.create_notification(
                user_id=user_id,
                notification_type=NotificationType.BROADCAST,
                title=title,
                message=message,
            )
            notifications.append(notification)
        return notifications

    @staticmethod
    async def process_scheduled_notifications() -> int:
        """Обрабатывает запланированные уведомления"""
        async with AsyncSessionLocal() as session:
            # Получаем уведомления для отправки
            result = await session.execute(
                select(Notification).where(
                    and_(
                        Notification.status == NotificationStatus.PENDING,
                        Notification.scheduled_at <= datetime.now(),
                    )
                )
            )
            notifications = result.scalars().all()

            sent_count = 0
            for notification in notifications:
                if await NotificationService.send_notification(notification.id):
                    sent_count += 1

            return sent_count

    @staticmethod
    async def cleanup_old_notifications(days: int = 30) -> int:
        """Удаляет старые уведомления"""
        async with AsyncSessionLocal() as session:
            cutoff_date = datetime.now() - timedelta(days=days)

            result = await session.execute(
                select(Notification).where(
                    and_(
                        Notification.created_at < cutoff_date,
                        Notification.status.in_(
                            [NotificationStatus.READ, NotificationStatus.FAILED]
                        ),
                    )
                )
            )
            old_notifications = result.scalars().all()

            for notification in old_notifications:
                await session.delete(notification)

            await session.commit()
            return len(old_notifications)
