"""
Роуты для взаимодействий между ролями
"""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.i18n import t
from app.repositories.user_repo import get_user
from app.roles import UserRole
from app.services.notification_service import interaction_service

router = Router()


# === УЧЕНИК → ПСИХОЛОГ ===
@router.message(Command("psy_request"))
async def student_psy_request(message: Message, state: FSMContext) -> None:
    """Ученик обращается к психологу"""
    user = await get_user(message.from_user.id)

    if not user or user.role != UserRole.STUDENT:
        await message.answer("❌ Эта команда доступна только ученикам.")
        return

    # Запрашиваем тему обращения
    await state.set_state("psy_request:theme")
    await message.answer(
        "🧑‍⚕️ Обращение к психологу\n\n" "Опишите кратко тему вашего обращения:", parse_mode="HTML"
    )


@router.message(F.text)
async def handle_psy_request_theme(message: Message, state: FSMContext) -> None:
    """Обрабатывает тему обращения к психологу"""
    current_state = await state.get_state()

    if current_state == "psy_request:theme":
        theme = message.text.strip()

        if len(theme) > 200:
            await message.answer("⚠️ Тема слишком длинная. Сократите до 200 символов.")
            return

        # Сохраняем тему
        await state.update_data(theme=theme)

        # Запрашиваем класс
        await state.set_state("psy_request:classroom")
        await message.answer("📚 Укажите ваш класс (например: 8А, 10Б):", parse_mode="HTML")


@router.message(F.text)
async def handle_psy_request_classroom(message: Message, state: FSMContext) -> None:
    """Обрабатывает класс для обращения к психологу"""
    current_state = await state.get_state()

    if current_state == "psy_request:classroom":
        classroom = message.text.strip()

        # Получаем сохранённую тему
        data = await state.get_data()
        theme = data.get("theme", "не указана")

        # Отправляем обращение
        await interaction_service.student_to_psychologist(
            student_id=message.from_user.id, theme=theme, classroom=classroom
        )

        # Очищаем состояние
        await state.clear()

        await message.answer(
            "✅ Ваше обращение отправлено психологу.\n" "Ожидайте ответа в ближайшее время.",
            parse_mode="HTML",
        )


# === УЧИТЕЛЬ → ТЕХПОДДЕРЖКА ===
@router.message(Command("support"))
async def teacher_support_request(message: Message, state: FSMContext) -> None:
    """Учитель обращается в техподдержку"""
    user = await get_user(message.from_user.id)

    if not user or user.role != UserRole.TEACHER:
        await message.answer("❌ Эта команда доступна только учителям.")
        return

    # Запрашиваем номер кабинета
    await state.set_state("support_request:room")
    await message.answer(
        "🛠 Обращение в техподдержку\n\n" "Укажите номер кабинета:", parse_mode="HTML"
    )


@router.message(F.text)
async def handle_support_request_room(message: Message, state: FSMContext) -> None:
    """Обрабатывает номер кабинета для заявки в техподдержку"""
    current_state = await state.get_state()

    if current_state == "support_request:room":
        room = message.text.strip()

        # Сохраняем номер кабинета
        await state.update_data(room=room)

        # Запрашиваем описание проблемы
        await state.set_state("support_request:description")
        await message.answer("📝 Опишите проблему подробно:", parse_mode="HTML")


@router.message(F.text)
async def handle_support_request_description(message: Message, state: FSMContext) -> None:
    """Обрабатывает описание проблемы для заявки в техподдержку"""
    current_state = await state.get_state()

    if current_state == "support_request:description":
        description = message.text.strip()

        if len(description) > 500:
            await message.answer("⚠️ Описание слишком длинное. Сократите до 500 символов.")
            return

        # Получаем сохранённый номер кабинета
        data = await state.get_data()
        room = data.get("room", "не указан")

        # Отправляем заявку
        await interaction_service.teacher_to_support(
            teacher_id=message.from_user.id, room=room, description=description
        )

        # Очищаем состояние
        await state.clear()


# === УЧИТЕЛЬ → ДИРЕКТОР ===
@router.message(Command("incident"))
async def teacher_incident_report(message: Message, state: FSMContext) -> None:
    """Учитель сообщает директору об инциденте"""
    user = await get_user(message.from_user.id)

    if not user or user.role != UserRole.TEACHER:
        await message.answer("❌ Эта команда доступна только учителям.")
        return

    # Запрашиваем класс
    await state.set_state("incident_report:classroom")
    await message.answer(
        "🚨 Сообщение об инциденте\n\n" "Укажите класс, где произошёл инцидент:", parse_mode="HTML"
    )


@router.message(F.text)
async def handle_incident_report_classroom(message: Message, state: FSMContext) -> None:
    """Обрабатывает класс для сообщения об инциденте"""
    current_state = await state.get_state()

    if current_state == "incident_report:classroom":
        classroom = message.text.strip()

        # Сохраняем класс
        await state.update_data(classroom=classroom)

        # Запрашиваем принятые меры
        await state.set_state("incident_report:measures")
        await message.answer(
            "📋 Опишите принятые меры (беседа, уведомление родителей и т.д.):", parse_mode="HTML"
        )


@router.message(F.text)
async def handle_incident_report_measures(message: Message, state: FSMContext) -> None:
    """Обрабатывает принятые меры для сообщения об инциденте"""
    current_state = await state.get_state()

    if current_state == "incident_report:measures":
        measures = message.text.strip()

        if len(measures) > 300:
            await message.answer("⚠️ Описание слишком длинное. Сократите до 300 символов.")
            return

        # Получаем сохранённый класс
        data = await state.get_data()
        classroom = data.get("classroom", "не указан")

        # Отправляем сообщение директору
        await interaction_service.teacher_to_director(
            teacher_id=message.from_user.id, classroom=classroom, measures=measures
        )

        # Очищаем состояние
        await state.clear()


# === АДМИНИСТРАТОР → МАССОВАЯ РАССЫЛКА ===
@router.message(Command("broadcast"))
async def admin_broadcast(message: Message, state: FSMContext) -> None:
    """Администратор делает массовую рассылку"""
    user = await get_user(message.from_user.id)

    if not user or user.role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
        await message.answer("❌ Эта команда доступна только администраторам.")
        return

    # Запрашиваем текст рассылки
    await state.set_state("broadcast:message")
    await message.answer(
        "📢 Массовая рассылка\n\n" "Введите текст сообщения для рассылки:", parse_mode="HTML"
    )


@router.message(F.text)
async def handle_broadcast_message(message: Message, state: FSMContext) -> None:
    """Обрабатывает текст для массовой рассылки"""
    current_state = await state.get_state()

    if current_state == "broadcast:message":
        broadcast_text = message.text.strip()

        if len(broadcast_text) > 1000:
            await message.answer("⚠️ Текст слишком длинный. Сократите до 1000 символов.")
            return

        # Отправляем рассылку
        await interaction_service.admin_broadcast(
            admin_id=message.from_user.id, message=broadcast_text
        )

        # Очищаем состояние
        await state.clear()


# === АДМИНИСТРАТОР → ОБЪЯВЛЕНИЕ СОБЫТИЯ ===
@router.message(Command("event"))
async def admin_event_announcement(message: Message, state: FSMContext) -> None:
    """Администратор объявляет событие"""
    user = await get_user(message.from_user.id)

    if not user or user.role not in [UserRole.ADMIN, UserRole.DIRECTOR]:
        await message.answer("❌ Эта команда доступна только администраторам.")
        return

    # Запрашиваем дату события
    await state.set_state("event_announcement:date")
    await message.answer(
        "📅 Объявление события\n\n" "Укажите дату события (например: 15 сентября):",
        parse_mode="HTML",
    )


@router.message(F.text)
async def handle_event_announcement_date(message: Message, state: FSMContext) -> None:
    """Обрабатывает дату для объявления события"""
    current_state = await state.get_state()

    if current_state == "event_announcement:date":
        date = message.text.strip()

        # Сохраняем дату
        await state.update_data(date=date)

        # Запрашиваем время
        await state.set_state("event_announcement:time")
        await message.answer("🕐 Укажите время события (например: 18:30):", parse_mode="HTML")


@router.message(F.text)
async def handle_event_announcement_time(message: Message, state: FSMContext) -> None:
    """Обрабатывает время для объявления события"""
    current_state = await state.get_state()

    if current_state == "event_announcement:time":
        time = message.text.strip()

        # Получаем сохранённую дату
        data = await state.get_data()
        date = data.get("date", "не указана")

        # Отправляем объявление
        await interaction_service.admin_event_announcement(
            admin_id=message.from_user.id, date=date, time=time
        )

        # Очищаем состояние
        await state.clear()


# === ОБРАБОТКА КНОПОК СОГЛАСИЯ ===
@router.callback_query(F.data == "consent_yes")
async def handle_consent_yes(callback: CallbackQuery) -> None:
    """Обрабатывает согласие родителя"""
    await callback.answer(t("psychologist.parent_consent_ok", "ru"), show_alert=True)

    # Здесь можно добавить логику для назначения консультации
    # await interaction_service.psychologist_to_student(...)


@router.callback_query(F.data == "consent_no")
async def handle_consent_no(callback: CallbackQuery) -> None:
    """Обрабатывает отказ родителя"""
    await callback.answer(t("psychologist.parent_consent_no", "ru"), show_alert=True)


@router.callback_query(F.data == "confirm_event")
async def handle_confirm_event(callback: CallbackQuery) -> None:
    """Обрабатывает подтверждение присутствия на событии"""
    await callback.answer(t("admin.event_confirm", "ru"), show_alert=True)
