"""
Универсальный сервис для уведомлений между ролями
"""

import asyncio
from typing import List

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t
from app.repositories.ticket_repo import create_ticket
from app.repositories.user_repo import get_user, get_users_by_role
from app.roles import UserRole


class NotificationService:
    """Сервис для отправки уведомлений между ролями"""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def notify_role(self, role: UserRole, message: str, **kwargs) -> int:
        """Отправляет уведомление всем пользователям с указанной ролью"""
        users = await get_users_by_role(role)
        sent_count = 0

        for user in users:
            try:
                await self.bot.send_message(
                    user.telegram_id, message.format(**kwargs), parse_mode="HTML"
                )
                sent_count += 1
                await asyncio.sleep(0.1)  # Задержка между отправками
            except Exception as e:
                print(f"Ошибка отправки уведомления пользователю {user.telegram_id}: {e}")

        return sent_count

    async def notify_admins(self, message: str, **kwargs) -> int:
        """Отправляет уведомление администраторам"""
        return await self.notify_role(UserRole.ADMIN, message, **kwargs)

    async def notify_teachers(self, message: str, **kwargs) -> int:
        """Отправляет уведомление учителям"""
        return await self.notify_role(UserRole.TEACHER, message, **kwargs)

    async def notify_parents(self, message: str, **kwargs) -> int:
        """Отправляет уведомление родителям"""
        return await self.notify_role(UserRole.PARENT, message, **kwargs)

    async def notify_students(self, message: str, **kwargs) -> int:
        """Отправляет уведомление ученикам"""
        return await self.notify_role(UserRole.STUDENT, message, **kwargs)

    async def notify_director(self, message: str, **kwargs) -> int:
        """Отправляет уведомление директору"""
        return await self.notify_role(UserRole.DIRECTOR, message, **kwargs)

    async def notify_psychologists(self, message: str, **kwargs) -> int:
        """Отправляет уведомление психологам"""
        return await self.notify_role(UserRole.PSYCHOLOGIST, message, **kwargs)


class InteractionService:
    """Сервис для взаимодействий между ролями"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.notification_service = NotificationService(bot)

    async def student_to_psychologist(
        self, student_id: int, theme: str, classroom: str = "не указан"
    ) -> None:
        """Ученик обращается к психологу"""
        student = await get_user(student_id)
        if not student:
            return

        # Создаём тикет
        ticket_data = {
            "title": f"Заявка к психологу: {theme}",
            "description": t("student.request_psy", "ru"),
            "author_id": student.id,
            "status": "open",
            "type": "psych_request",
            "priority": "normal",
        }

        ticket = await create_ticket(**ticket_data)

        # Уведомляем психологов
        alert_message = t("psychologist.student_alert", "ru").format(
            student=f"{student.first_name} {student.last_name or ''}",
            classroom=classroom,
            theme=theme,
        )

        await self.notification_service.notify_psychologists(alert_message)

        # Подтверждение ученику
        confirm_message = t("student.psy_request_confirm", "ru")
        await self.bot.send_message(student_id, confirm_message)

    async def teacher_to_support(self, teacher_id: int, room: str, description: str) -> None:
        """Учитель обращается в техподдержку"""
        teacher = await get_user(teacher_id)
        if not teacher:
            return

        # Создаём тикет
        ticket_data = {
            "title": f"Техподдержка: кабинет {room}",
            "description": description,
            "author_id": teacher.id,
            "status": "open",
            "type": "support_request",
            "priority": "normal",
        }

        ticket = await create_ticket(**ticket_data)

        # Уведомляем техподдержку (админов)
        support_message = t("support.request_received", "ru").format(
            description=description,
            room=room,
            teacher=f"{teacher.first_name} {teacher.last_name or ''}",
        )

        await self.notification_service.notify_admins(support_message)

        # Подтверждение учителю
        confirm_message = t("teacher.support_request_confirm", "ru").format(time="16:00")
        await self.bot.send_message(teacher_id, confirm_message)

    async def teacher_to_director(self, teacher_id: int, classroom: str, measures: str) -> None:
        """Учитель сообщает директору об инциденте"""
        teacher = await get_user(teacher_id)
        if not teacher:
            return

        # Создаём тикет
        ticket_data = {
            "title": f"Инцидент в {classroom}",
            "description": t("teacher.incident_report", "ru").format(classroom=classroom),
            "author_id": teacher.id,
            "status": "open",
            "type": "incident_report",
            "priority": "high",
        }

        ticket = await create_ticket(**ticket_data)

        # Уведомляем директора
        director_message = t("director.incident_notify", "ru").format(
            classroom=classroom, measures=measures
        )

        await self.notification_service.notify_director(director_message)

        # Подтверждение учителю
        thank_message = t("teacher.incident_teacher_thank", "ru")
        await self.bot.send_message(teacher_id, thank_message)

    async def psychologist_to_parent(self, parent_id: int, child_name: str) -> None:
        """Психолог запрашивает согласие родителя"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=t("parent.consent_button_yes", "ru"), callback_data="consent_yes"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=t("parent.consent_button_no", "ru"), callback_data="consent_no"
                    )
                ],
            ]
        )

        message = t("psychologist.parent_consent_request", "ru")
        await self.bot.send_message(parent_id, message, reply_markup=keyboard)

    async def admin_broadcast(
        self, admin_id: int, message: str, target_roles: List[UserRole] = None
    ) -> int:
        """Администратор делает массовую рассылку"""
        if target_roles is None:
            target_roles = [UserRole.STUDENT, UserRole.TEACHER, UserRole.PARENT]

        total_sent = 0
        for role in target_roles:
            sent = await self.notification_service.notify_role(role, message)
            total_sent += sent

        # Подтверждение администратору
        confirm_message = t("admin.broadcast_sent", "ru").format(count=total_sent)
        await self.bot.send_message(admin_id, confirm_message)

        return total_sent

    async def admin_event_announcement(self, admin_id: int, date: str, time: str) -> None:
        """Администратор объявляет событие"""
        message = t("admin.event_announce", "ru").format(date=date, time=time)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=t("admin.confirm_presence", "ru"), callback_data="confirm_event"
                    )
                ]
            ]
        )

        # Отправляем всем родителям
        await self.notification_service.notify_parents(message, reply_markup=keyboard)

        # Подтверждение администратору
        confirm_message = t("admin.broadcast_sent", "ru").format(count="все родители")
        await self.bot.send_message(admin_id, confirm_message)

    async def support_to_teacher(self, teacher_id: int, ticket_id: int, description: str) -> None:
        """Техподдержка отвечает учителю"""
        message = t("support.request_processed", "ru").format(
            ticket_id=ticket_id, description=description
        )

        await self.bot.send_message(teacher_id, message)

    async def psychologist_to_student(
        self, student_id: int, date: str, time: str, location: str
    ) -> None:
        """Психолог назначает консультацию ученику"""
        message = t("psychologist.consultation_scheduled", "ru").format(
            date=date, time=time, location=location
        )

        await self.bot.send_message(student_id, message)


# Глобальные экземпляры сервисов
notification_service: NotificationService = None
interaction_service: InteractionService = None


def init_notification_services(bot: Bot) -> None:
    """Инициализирует глобальные сервисы уведомлений"""
    global notification_service, interaction_service
    notification_service = NotificationService(bot)
    interaction_service = InteractionService(bot)
