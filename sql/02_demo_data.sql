-- Демо-данные для SchoolBot
-- Вставка тестовых пользователей и данных

-- Тестовые пользователи для разных ролей
INSERT INTO users (tg_id, username, first_name, last_name, role, login, password, used, theme, seen_intro) 
VALUES 
    -- Администратор
    (123456789, 'admin_user', 'Администратор', 'Системы', 'admin', 'admin', 'admin123', false, 'dark', true),
    
    -- Директор
    (234567890, 'director_user', 'Иван', 'Петров', 'director', 'director', 'dir123', false, 'light', true),
    
    -- Учителя
    (345678901, 'teacher1', 'Мария', 'Иванова', 'teacher', 'teacher1', 'teach123', false, 'light', true),
    (456789012, 'teacher2', 'Александр', 'Сидоров', 'teacher', 'teacher2', 'teach456', false, 'dark', true),
    
    -- Психолог
    (567890123, 'psychologist', 'Елена', 'Смирнова', 'psych', 'psych1', 'psych123', false, 'light', true),
    
    -- Родители
    (678901234, 'parent1', 'Анна', 'Кузнецова', 'parent', 'parent1', 'parent123', false, 'light', false),
    (789012345, 'parent2', 'Сергей', 'Волков', 'parent', 'parent2', 'parent456', false, 'light', false),
    
    -- Ученики
    (890123456, 'student1', 'Алиса', 'Петрова', 'student', 'student1', 'stud123', false, 'light', false),
    (901234567, 'student2', 'Максим', 'Козлов', 'student', 'student2', 'stud456', false, 'dark', false)
ON CONFLICT (tg_id) DO NOTHING;

-- Тестовые заметки учителей
INSERT INTO notes (user_id, title, content, is_private)
SELECT 
    u.id,
    'План урока по математике',
    'Тема: Квадратные уравнения. Цель: изучить способы решения квадратных уравнений. Задачи: 1) Повторить формулы, 2) Решить примеры, 3) Дать домашнее задание.',
    true
FROM users u WHERE u.role = 'teacher' LIMIT 1;

INSERT INTO notes (user_id, title, content, is_private)
SELECT 
    u.id,
    'Методические заметки',
    'Использование интерактивных методов обучения показало хорошие результаты. Рекомендую применять чаще.',
    false
FROM users u WHERE u.role = 'teacher' LIMIT 1;

-- Тестовые тикеты в техподдержку
INSERT INTO tickets (user_id, title, description, status, priority)
SELECT 
    u.id,
    'Проблема с проектором',
    'В кабинете 205 не работает проектор. Нужна срочная замена лампы.',
    'open',
    'high'
FROM users u WHERE u.role = 'teacher' LIMIT 1;

INSERT INTO tickets (user_id, title, description, status, priority)
SELECT 
    u.id,
    'Доступ к электронному журналу',
    'Не могу войти в систему электронного журнала. Ошибка авторизации.',
    'pending',
    'medium'
FROM users u WHERE u.role = 'teacher' OFFSET 1 LIMIT 1;

-- Тестовые запросы к психологу
INSERT INTO psych_requests (user_id, description, status, priority)
SELECT 
    u.id,
    'Консультация по поведению ученика 7А класса. Ребенок стал агрессивным, отказывается выполнять задания.',
    'pending',
    'high'
FROM users u WHERE u.role = 'teacher' LIMIT 1;

INSERT INTO psych_requests (user_id, description, status, priority)
SELECT 
    u.id,
    'Нужна помощь в адаптации после перевода из другой школы.',
    'pending',
    'medium'
FROM users u WHERE u.role = 'parent' LIMIT 1;

-- Тестовые медиа-запросы
INSERT INTO media_requests (user_id, request_type, description, status)
SELECT 
    u.id,
    'certificate',
    'Справка об обучении для предоставления в спортивную секцию.',
    'pending'
FROM users u WHERE u.role = 'parent' LIMIT 1;

INSERT INTO media_requests (user_id, request_type, description, status)
SELECT 
    u.id,
    'report',
    'Академическая справка для перевода в другое учебное заведение.',
    'processing'
FROM users u WHERE u.role = 'student' LIMIT 1;

-- Тестовые задачи от директора
INSERT INTO tasks (user_id, title, description, status, priority, due_date)
SELECT 
    u.id,
    'Подготовка к родительскому собранию',
    'Подготовить презентацию по итогам четверти, составить отчет об успеваемости класса.',
    'pending',
    'high',
    NOW() + INTERVAL '7 days'
FROM users u WHERE u.role = 'teacher' LIMIT 1;

INSERT INTO tasks (user_id, title, description, status, priority, due_date)
SELECT 
    u.id,
    'Обновление методических материалов',
    'Пересмотреть и обновить методические материалы в соответствии с новыми стандартами.',
    'in_progress',
    'medium',
    NOW() + INTERVAL '14 days'
FROM users u WHERE u.role = 'teacher' OFFSET 1 LIMIT 1;

-- Тестовые рассылки
INSERT INTO broadcasts (user_id, title, message, target_role, status, sent_at)
SELECT 
    u.id,
    'Собрание педагогического коллектива',
    'Уважаемые коллеги! Напоминаем о собрании учителей сегодня в 15:00 в актовом зале. Повестка: подготовка к родительским собраниям.',
    'teacher',
    'sent',
    NOW() - INTERVAL '1 hour'
FROM users u WHERE u.role = 'admin' LIMIT 1;

INSERT INTO broadcasts (user_id, title, message, target_role, status)
SELECT 
    u.id,
    'Информация для родителей',
    'Дорогие родители! Сообщаем о проведении дня открытых дверей 15 мая с 10:00 до 16:00.',
    'parent',
    'draft'
FROM users u WHERE u.role = 'director' LIMIT 1;

-- Тестовые уведомления
INSERT INTO notifications (user_id, title, message, notification_type, is_read)
SELECT 
    u.id,
    'Новое задание',
    'Вам назначено новое задание от администрации.',
    'task',
    false
FROM users u WHERE u.role = 'teacher';

INSERT INTO notifications (user_id, title, message, notification_type, is_read)
SELECT 
    u.id,
    'Добро пожаловать!',
    'Добро пожаловать в SchoolBot! Система поможет вам в ежедневной работе.',
    'welcome',
    false
FROM users u WHERE u.seen_intro = false;
