# commands.py
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ConversationHandler, filters
import sqlite3
from datetime import datetime
from config import ADMIN_USERS, ADMIN_CHAT_ID

# Определение этапов для ConversationHandler'ов
ENTER_NAME, ENTER_ORGANIZATION, ENTER_DESCRIPTION, ENTER_COMMENT = range(4)
ENTER_TICKET_ID_FEEDBACK, ENTER_FEEDBACK = range(2)
ENTER_TICKET_ID_COMMENT, ENTER_ADMIN_COMMENT = range(2)
ENTER_TICKET_ID_NEW_COMMENT, ENTER_NEW_COMMENT = range(2)
ENTER_TICKET_ID_STATUS, ENTER_STATUS = range(2)
ENTER_TICKET_ID_DELETE = range(1)
ENTER_TICKET_ID = range(1)

# Функция для создания базы данных тикетов
def create_database():
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        client_name TEXT,
        organization TEXT,
        description TEXT,
        status TEXT DEFAULT 'Открыт ⌛',
        comments TEXT DEFAULT '',
        feedback TEXT DEFAULT ''
    )
    ''')
    conn.commit()
    conn.close()


async def show_main_menu(update: Update, context):
    user_id = str(update.message.from_user.id)

    # Если пользователь не администратор, добавляем кнопки "Новый тикет" и "Оставить отзыв"
    if user_id not in ADMIN_USERS:
        keyboard = [
            [KeyboardButton("Новый тикет"), KeyboardButton("Оставить отзыв")],
            [KeyboardButton("Мои тикеты"), KeyboardButton("Просмотреть тикет")],
            [KeyboardButton("Добавить комментарий"), KeyboardButton("Помощь")]
        ]
    else:
        # Если пользователь администратор, убираем эти кнопки
        keyboard = [
            [KeyboardButton("Просмотреть тикет")],
            [KeyboardButton("Добавить комментарий"), KeyboardButton("Помощь")]
        ]

        # Добавляем дополнительные админские команды
        keyboard.extend([
            [KeyboardButton("Удалить все закрытые тикеты"), KeyboardButton("Изменить статус тикета")],
            [KeyboardButton("Список всех тикетов"), KeyboardButton("Удалить тикет")]
        ])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text('Выберите команду:', reply_markup=reply_markup)

# Обновляем команду /start для отображения главного меню
async def start(update: Update, context):
    user_id = str(update.message.from_user.id)
    await show_main_menu(update, context)

async def help_command(update: Update, context):
    user_id = str(update.message.from_user.id)
    help_text = (
        "/start - Начать работу с ботом\n"
        "/cancel - Отменить действие\n"
        "/menu - меню бота\n"
        "Новый тикет - Создать новый тикет\n"
        "Оставить отзыв - Оставить отзыв о тикете\n"
        "Мои тикеты - Показать ваши тикеты\n"
        "Просмотреть тикеты - Показать статус и историю сообщений тикета\n"
        "Добавить комментарий - Добавить комментарий к тикету\n"
        "Помощь - список доступных команд\n"
    )

    if user_id in ADMIN_USERS:
        help_text += (
            "Ответить на тикет - Ответить на тикет клиента\n"
            "Изменить статус - Изменить статус тикета\n"
            "Список всех тикетов - Показать все тикеты\n"
            "Удалить тикет - Удалить тикет\n"
        )

    await update.message.reply_text(help_text)

# Команды для создания тикетов
async def new_ticket_start(update: Update, context):
    user_id = str(update.message.from_user.id)

    # Если пользователь администратор, отменяем создание тикета
    if user_id in ADMIN_USERS:
        await update.message.reply_text('Администраторы не могут создавать тикеты.')
        return ConversationHandler.END

    await update.message.reply_text('Пожалуйста, введите ваше имя:\n/cancel - отменить')
    return ENTER_NAME

async def enter_name(update: Update, context):
    context.user_data['client_name'] = update.message.text
    await update.message.reply_text('Введите название вашей организации:\n/cancel - отменить')
    return ENTER_ORGANIZATION

async def enter_organization(update: Update, context):
    context.user_data['organization'] = update.message.text
    await update.message.reply_text('Введите описание вашей проблемы:\n/cancel - отменить')
    return ENTER_DESCRIPTION

async def enter_description(update: Update, context):
    context.user_data['description'] = update.message.text
    await update.message.reply_text('Введите комментарий к вашей проблеме:\n/cancel - отменить')
    return ENTER_COMMENT

async def enter_comment(update: Update, context):
    context.user_data['comment'] = update.message.text

    # Извлечение данных пользователя из контекста
    chat_id = update.message.chat_id
    client_name = context.user_data['client_name']
    organization = context.user_data['organization']
    description = context.user_data['description']
    initial_comment = context.user_data['comment']

    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
    initial_comment = f'{timestamp} {client_name}: {initial_comment}\n'

    # Добавляем тикет в базу данных
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO tickets (chat_id, client_name, organization, description, comments)
    VALUES (?, ?, ?, ?, ?)
    ''', (chat_id, client_name, organization, description, initial_comment))
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Уведомляем пользователя и администратора
    await update.message.reply_text(f'Тикет создан успешно! ID тикета: {ticket_id}')
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID,
                                   text=f'Новый тикет #{ticket_id}:\nИмя: {client_name}\nОрганизация: {organization}\nТема: {description}\nКомментарий: {initial_comment}')
    return ConversationHandler.END

# Команда для просмотра тикетов пользователя
async def my_tickets(update: Update, context):
    chat_id = update.message.chat_id
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, description, status FROM tickets WHERE chat_id = ?', (chat_id,))
    results = cursor.fetchall()
    conn.close()

    if results:
        tickets_list = '\n'.join([f'ID: {row[0]}, Тема: {row[1]}, Статус: {row[2]}' for row in results])
        await update.message.reply_text(f'Ваши тикеты:\n{tickets_list}')
    else:
        await update.message.reply_text('У вас нет тикетов.')

# Команда для просмотра тикета
async def ticket_start(update: Update, context):
    await update.message.reply_text('Пожалуйста, введите ID тикета:\n/cancel - отменить')
    return ENTER_TICKET_ID

async def enter_ticket_id(update: Update, context):
    ticket_id = update.message.text
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    if not is_ticket_owner_or_admin(ticket_id, chat_id, user_id):
        await update.message.reply_text('У вас нет прав на просмотр этого тикета.')
        return ConversationHandler.END

    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT status, comments, feedback FROM tickets WHERE id = ?', (ticket_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        status, comments, feedback = result
        comments = comments.strip()
        feedback = feedback.strip()

        ticket_details = f'Статус тикета {ticket_id}: {status}\n\n'
        if comments:
            ticket_details += f'История комментариев:\n{comments}\n\n'
        else:
            ticket_details += 'Комментарии отсутствуют.\n\n'
        if feedback:
            ticket_details += f'История отзывов:\n{feedback}'
        else:
            ticket_details += 'Отзывы отсутствуют.'

        await update.message.reply_text(ticket_details)
    else:
        await update.message.reply_text('Тикет не найден.')

    return ConversationHandler.END

# Команда для добавления отзыва к тикету
async def feedback_start(update: Update, context):
    await update.message.reply_text('Пожалуйста, введите ID тикета:\n/cancel - отменить')
    return ENTER_TICKET_ID_FEEDBACK


async def enter_ticket_id_feedback(update: Update, context):
    ticket_id = update.message.text
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    # Подключение к базе данных для проверки существования тикета и статуса
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id, status, feedback FROM tickets WHERE id = ?', (ticket_id,))
    result = cursor.fetchone()

    # Проверяем, существует ли тикет
    if result:
        ticket_owner_chat_id, status, existing_feedback = result

        # Проверяем, является ли текущий пользователь владельцем тикета
        if ticket_owner_chat_id != chat_id:
            await update.message.reply_text('Вы не можете оставить отзыв.')
            conn.close()
            return ConversationHandler.END

        # Проверка статуса тикета: отзыв можно оставить только на закрытый тикет
        if status != "Закрыт ✅":
            await update.message.reply_text('Отзыв можно оставить только на закрытые тикеты.')
            conn.close()
            return ConversationHandler.END

        # Проверка, что отзыв уже не был оставлен
        if existing_feedback.strip():
            await update.message.reply_text('Вы уже оставили отзыв для этого тикета. Повторный отзыв невозможен.')
            conn.close()
            return ConversationHandler.END

        # Если всё в порядке, продолжаем процесс ввода отзыва
        context.user_data['ticket_id'] = ticket_id
        await update.message.reply_text('Введите ваш отзыв:\n/cancel - отменить')
    else:
        await update.message.reply_text('Тикет с таким ID не найден.')

    conn.close()
    return ENTER_FEEDBACK


async def enter_feedback(update: Update, context):
    ticket_id = context.user_data['ticket_id']
    feedback_text = update.message.text
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Connect to the database and fetch the client's name for the ticket
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT client_name, feedback FROM tickets WHERE id = ?', (ticket_id,))
    result = cursor.fetchone()

    if result:
        client_name, existing_feedback = result

        # Format the feedback with the client's name from the database
        feedback_comment = f'{timestamp} {client_name}: {feedback_text}\n'
        updated_feedback = existing_feedback + feedback_comment

        # Update the feedback in the database
        cursor.execute('UPDATE tickets SET feedback = ? WHERE id = ?', (updated_feedback, ticket_id))
        conn.commit()

        # Notify the user that the feedback has been saved
        await update.message.reply_text('Ваш отзыв сохранен! Спасибо за ваш отзыв.')

        # Notify the admin about the new feedback
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f'Новый отзыв к тикету #{ticket_id}:\n{feedback_comment}')
    else:
        await update.message.reply_text('Тикет с таким ID не найден. Пожалуйста, попробуйте снова.')

    conn.close()
    return ConversationHandler.END

# Проверка принадлежности тикета пользователю
def is_ticket_owner_or_admin(ticket_id, chat_id, user_id):
    # Если пользователь админ, сразу возвращаем True
    if str(user_id) in ADMIN_USERS:
        return True

    # Для обычных пользователей проверяем, владеют ли они тикетом
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id FROM tickets WHERE id = ?', (ticket_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0] == chat_id
    return False

#  Добавление комментария к тикету
async def add_new_comment_start(update: Update, context):
    await update.message.reply_text('Пожалуйста, введите ID тикета, к которому хотите добавить комментарий:\n/cancel - отменить')
    return ENTER_TICKET_ID_NEW_COMMENT

async def enter_ticket_id_new_comment(update: Update, context):
    ticket_id = update.message.text
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    # Проверка, что тикет не закрыт
    if is_ticket_closed(ticket_id):
        await update.message.reply_text('Вы не можете добавить комментарий к закрытому тикету.')
        return ConversationHandler.END

    # Проверка принадлежности тикета клиенту или админу
    if not is_ticket_owner_or_admin(ticket_id, chat_id, user_id):
        await update.message.reply_text('У вас нет прав на добавление комментария к этому тикету.')
        return ConversationHandler.END

    # Сохраняем ticket_id для дальнейшего использования
    context.user_data['ticket_id'] = ticket_id
    await update.message.reply_text('Введите ваш комментарий:\n/cancel - отменить')
    return ENTER_NEW_COMMENT

async def enter_new_comment(update: Update, context):
    ticket_id = context.user_data['ticket_id']
    comment = update.message.text
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Подключаемся к базе данных, чтобы получить имя клиента и историю комментариев
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id, client_name, comments FROM tickets WHERE id = ?', (ticket_id,))
    result = cursor.fetchone()

    if result:
        ticket_owner_chat_id, client_name, existing_comments = result

        # Определяем, кто добавляет комментарий: админ или клиент
        if str(user_id) in ADMIN_USERS:
            sender_name = ADMIN_USERS[str(user_id)]
            comment_entry = f'{timestamp} {sender_name}: {comment}\n'
        else:
            sender_name = client_name  # Имя клиента
            comment_entry = f'{timestamp} {sender_name}: {comment}\n'

        # Обновляем историю комментариев
        updated_comments = existing_comments + comment_entry
        cursor.execute('UPDATE tickets SET comments = ? WHERE id = ?', (updated_comments, ticket_id))
        conn.commit()

        # Отправляем уведомления:
        if str(user_id) in ADMIN_USERS:
            # Уведомляем клиента о комментарии администратора
            await context.bot.send_message(chat_id=ticket_owner_chat_id, text=f'Ответ на ваш тикет #{ticket_id}:\n{comment_entry}')
            await update.message.reply_text('Комментарий добавлен и отправлен клиенту.')
        else:
            # Уведомляем администратора о комментарии клиента
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f'Новый комментарий к тикету #{ticket_id} от клиента:\n{comment_entry}')
            await update.message.reply_text('Ваш комментарий добавлен и отправлен администратору.')

    else:
        await update.message.reply_text('Тикет с таким ID не найден.')

    conn.close()
    return ConversationHandler.END


# Админские команды

# Декоратор для проверки, что команда исполняется админом
def admin_only(func):
    async def wrapper(update: Update, context):
        user_id = str(update.message.from_user.id)
        if user_id not in ADMIN_USERS:
            await update.message.reply_text('Эта команда доступна только администраторам.')
            return
        return await func(update, context)
    return wrapper

@admin_only
async def admin_change_status_start(update: Update, context):
    await update.message.reply_text('Пожалуйста, введите ID тикета:\n/cancel - отменить')
    return ENTER_TICKET_ID_STATUS

async def enter_ticket_id_status(update: Update, context):
    context.user_data['ticket_id'] = update.message.text

    # Отображаем меню с кнопками для выбора статуса
    keyboard = [
        ["Открыт ⌛", "Закрыт ✅"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text('Выберите новый статус для тикета:\n/cancel - отменить', reply_markup=reply_markup)
    return ENTER_STATUS

@admin_only
async def enter_status(update: Update, context):
    new_status = update.message.text  # Получаем выбранный статус из нажатой кнопки
    ticket_id = context.user_data['ticket_id']

    # Проверяем, что админ выбрал либо "Открыт ⌛", либо "Закрыт ✅"
    if new_status not in ["Открыт ⌛", "Закрыт ✅"]:
        await update.message.reply_text('Неверный выбор. Пожалуйста, выберите статус из предложенных вариантов.')
        return ENTER_STATUS

    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id FROM tickets WHERE id = ?', (ticket_id,))
    result = cursor.fetchone()

    if result:
        chat_id = result[0]
        cursor.execute('UPDATE tickets SET status = ? WHERE id = ?', (new_status, ticket_id))
        conn.commit()

        # Уведомление пользователя о новом статусе
        await context.bot.send_message(chat_id=chat_id, text=f'Статус вашего тикета #{ticket_id} был изменён на: {new_status}')
        await update.message.reply_text(f'Статус тикета #{ticket_id} обновлен на {new_status}.')

        # Возвращаем основное меню после обновления статуса
        await show_main_menu(update, context)
    else:
        await update.message.reply_text('Тикет с таким ID не найден.')
        # Возвращаем основное меню при ошибке
        await show_main_menu(update, context)

    conn.close()
    return ConversationHandler.END

def is_ticket_closed(ticket_id):
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT status FROM tickets WHERE id = ?', (ticket_id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0] == "Закрыт ✅":
        return True
    return False

@admin_only
async def admin_delete_ticket_start(update: Update, context):
    choice = update.message.text

    if choice == "Удалить все закрытые тикеты":
        await delete_all_closed_tickets(update, context)
    else:
        await update.message.reply_text('Пожалуйста, введите ID тикета для удаления:\n/cancel - отменить')
        return ENTER_TICKET_ID_DELETE

@admin_only
async def delete_all_closed_tickets(update: Update, context):
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()

    cursor.execute('SELECT id, chat_id FROM tickets WHERE status = "Закрыт ✅"')
    closed_tickets = cursor.fetchall()

    if closed_tickets:
        for ticket_id, chat_id in closed_tickets:
            cursor.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
            await context.bot.send_message(chat_id=chat_id, text=f'Ваш тикет #{ticket_id} был удален администратором.')

        conn.commit()
        await update.message.reply_text(f'Все закрытые тикеты успешно удалены.')
    else:
        await update.message.reply_text('Нет закрытых тикетов для удаления.')

    conn.close()
    return ConversationHandler.END

@admin_only
async def enter_ticket_id_delete(update: Update, context):
    ticket_id = update.message.text

    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id FROM tickets WHERE id = ?', (ticket_id,))
    result = cursor.fetchone()

    if result:
        chat_id = result[0]
        cursor.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
        conn.commit()

        # Уведомление пользователя о удалении тикета
        await context.bot.send_message(chat_id=chat_id, text=f'Ваш тикет #{ticket_id} был удален администратором.')
        await update.message.reply_text(f'Тикет #{ticket_id} успешно удален.')
    else:
        await update.message.reply_text('Тикет с таким ID не найден.')

    conn.close()
    return ConversationHandler.END

@admin_only
async def admin_show_all_tickets(update: Update, context):
    conn = sqlite3.connect('tickets.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, client_name, organization, description, status FROM tickets')
    results = cursor.fetchall()
    conn.close()

    if results:
        tickets_list = '\n'.join([f'ID: {row[0]}, {row[1]}, {row[2]}, {row[3]}, Статус: {row[4]}' for row in results])
        await update.message.reply_text(f'Все тикеты:\n{tickets_list}')
    else:
        await update.message.reply_text('Нет тикетов.')

# Функция для отмены процесса
async def cancel(update: Update, context):
    # Сообщаем пользователю, что операция отменена
    await update.message.reply_text('Операция отменена.')

    # Возвращаем пользователя в главное меню после отмены
    await show_main_menu(update, context)

    # Завершаем разговор и сбрасываем все состояния
    return ConversationHandler.END