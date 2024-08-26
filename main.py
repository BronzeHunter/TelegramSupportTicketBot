from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters
from commands import (
    start, help_command, new_ticket_start, enter_name, enter_organization, enter_description, enter_comment, my_tickets,
    ticket_start, enter_ticket_id, feedback_start, enter_ticket_id_feedback, enter_feedback, admin_change_status_start, enter_ticket_id_status, enter_status,
    admin_delete_ticket_start, enter_ticket_id_delete, cancel,add_new_comment_start, enter_ticket_id_new_comment, enter_new_comment,
    show_main_menu, admin_show_all_tickets, is_ticket_closed, delete_all_closed_tickets
)
from config import BOT_TOKEN
from commands import create_database

# Определение этапов для ConversationHandler'ов
ENTER_NAME, ENTER_ORGANIZATION, ENTER_DESCRIPTION, ENTER_COMMENT = range(4)
ENTER_TICKET_ID_FEEDBACK, ENTER_FEEDBACK = range(2)
ENTER_TICKET_ID_COMMENT, ENTER_ADMIN_COMMENT = range(2)
ENTER_TICKET_ID_NEW_COMMENT, ENTER_NEW_COMMENT = range(2)
ENTER_TICKET_ID_STATUS, ENTER_STATUS = range(2)
ENTER_TICKET_ID_DELETE = range(1)
ENTER_TICKET_ID = range(1)

# Функция для настройки ConversationHandler'ов
def setup_conversation_handlers():
    return [
        # Создание нового тикета
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^Новый тикет$'), new_ticket_start)],
            states={
                ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
                ENTER_ORGANIZATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_organization)],
                ENTER_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_description)],
                ENTER_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_comment)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        ),
        # Добавление отзыва
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^Оставить отзыв$'), feedback_start)],
            states={
                ENTER_TICKET_ID_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_ticket_id_feedback)],
                ENTER_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_feedback)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        ),
        # Изменение статуса тикета
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^Изменить статус тикета$'), admin_change_status_start)],
            states={
                ENTER_TICKET_ID_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_ticket_id_status)],
                ENTER_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_status)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        ),
        # Удаление тикета
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^Удалить тикет$'), admin_delete_ticket_start)],
            states={
                ENTER_TICKET_ID_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_ticket_id_delete)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        ),
        # Просмотр тикета
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^Просмотреть тикет$'), ticket_start)],
            states={
                ENTER_TICKET_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_ticket_id)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        ),
        # Добавление комментария
        ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^Добавить комментарий$'), add_new_comment_start)],
            states={
                ENTER_TICKET_ID_NEW_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_ticket_id_new_comment)],
                ENTER_NEW_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_new_comment)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        ),
    ]

# Главная функция запуска бота
def main():
    create_database()
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация хендлеров
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('mytickets', my_tickets))
    application.add_handler(CommandHandler('menu', show_main_menu))  # Команда для отображения меню
    application.add_handler(MessageHandler(filters.Regex('^(Мои тикеты)$'), my_tickets))
    application.add_handler(MessageHandler(filters.Regex('^(Список всех тикетов)$'), admin_show_all_tickets))
    application.add_handler(MessageHandler(filters.Regex('^(Помощь)$'), help_command))
    application.add_handler(MessageHandler(filters.Regex('^(Удалить все закрытые тикеты)$'), delete_all_closed_tickets))
    # Добавляем все conversation handlers
    for handler in setup_conversation_handlers():
        application.add_handler(handler)

    application.run_polling()

if __name__ == '__main__':
    main()
