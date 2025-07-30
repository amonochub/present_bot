# Demo Data Seeding Documentation

## Overview
The demo data seeding feature automatically populates the database with realistic sample data for each role, making the SchoolBot immediately usable for demonstrations and presentations.

## What Gets Created

### 👩‍🏫 Teacher Role - Notes
- **3 sample notes** created by teachers:
  - "Петров Илья - Отличный ответ на уроке" (teacher01)
  - "Сидорова Анна - Не сдала домашнюю работу" (teacher01)
  - "Ким Даниил - Помог однокласснику с задачей" (teacher02)

### 🛠 IT Tickets
- **2 IT support tickets**:
  - "Не включается проектор" (teacher01, status: open)
  - "Не печатает принтер" (teacher02, status: in_progress)

### 🎬 Media Center Requests
- **1 media request**:
  - "Съёмка концерта 5-го класса" (teacher01, event_date: today + 7 days)

### 🧑‍⚕️ Psychologist Requests
- **2 psychological requests**:
  - "Меня дразнят одноклассники, не хочу идти в школу" (student02)
  - "Ругался с родителями, чувствую стресс" (student03)

### 📈 Director Tasks
- **2 director assignments**:
  - "Подготовить отчёт по успеваемости" (assigned to teacher01)
  - "Обновить расписание в МЭШ" (assigned to teacher02)

### 🏛 Admin Role - Broadcasts
- **1 mass broadcast**: "Собрание учителей" (already delivered)
- **Content**: "Уважаемые коллеги! Напоминаем о собрании учителей сегодня в 15:00 в актовом зале. Повестка: подготовка к родительским собраниям."
- **Target**: All teachers
- **Status**: Delivered

## Technical Implementation

### Database Seeding Function
```python
async def seed_demo(conn):
    """
    Populates tables with examples if they're empty.
    """
    # Check if data already exists
    note_exists = await conn.execute(select(Note.id).limit(1))
    if note_exists.first():
        return  # Already seeded

    # User IDs (based on insertion order)
    teacher1 = 1   # teacher01
    teacher2 = 2   # teacher02
    student2 = 23  # student02
    student3 = 24  # student03
```

### User ID Mapping
The seeding uses specific user IDs based on the DEMO_USERS insertion order:
- **teacher01** → ID 1
- **teacher02** → ID 2
- **student02** → ID 23
- **student03** → ID 24

### Data Relationships
- Notes are linked to teachers via `teacher_id`
- Tickets are linked to authors via `author_id`
- Media requests are linked to teachers via `author_id`
- Psych requests are linked to students via `from_id`
- Tasks are linked to directors (author_id=1) and assigned teachers

## Usage Scenarios

### For Demo Account (/tour)
1. **Teacher Role**: Shows 3 notes in "📝 Мои заметки"
2. **Admin Role**: Shows 2 IT tickets in ticket management
3. **Director Role**: Shows KPI with "0/2 tasks completed"
4. **Psychologist Role**: Shows 2 psychological requests

### For Individual Role Testing
- **teacher01/teacher**: Can see their 2 notes
- **teacher02/teacher**: Can see their 1 note
- **admin01/admin**: Can manage IT tickets
- **student02/student**: Has a psychological request
- **student03/student**: Has a psychological request

## Database Schema Compatibility

### Notes Table
```sql
notes (id, teacher_id, student_name, text, created_at, updated_at)
```

### Tickets Table
```sql
tickets (id, author_id, title, file_id, status, created_at)
```

### Media Requests Table
```sql
media_requests (id, author_id, event_date, comment, file_id, status, created_at)
```

### Psych Requests Table
```sql
psych_requests (id, from_id, content_id, text, status, created_at)
```

### Tasks Table
```sql
tasks (id, title, description, status, priority, due_date, author_id, assigned_to_id, created_at, updated_at)
```

## Testing

### Manual Testing Steps
1. Start the bot: `python -m app.bot`
2. Login as demo01/demo
3. Execute `/tour`
4. Verify each role shows appropriate demo data
5. Test role-specific functionality

### Automated Testing
```bash
# Test demo data seeding
python test_demo_seed.py
```

## Reset Demo Data
To reset and recreate demo data:
```bash
# Stop containers and remove volumes
docker-compose down -v

# Rebuild and start
docker-compose up --build
```

## Future Enhancements
- Add more diverse demo data
- Add demo data for parent role (PDF certificates)
- Add demo data for student role (assignments)
- Add demo broadcast messages for admin role
- Add demo statistics and metrics

## Troubleshooting

### Common Issues
1. **No demo data appears**: Check if database was recreated
2. **Wrong user IDs**: Verify DEMO_USERS order hasn't changed
3. **Missing relationships**: Check foreign key constraints
4. **Enum errors**: Verify TaskStatus enum usage

### Debug Commands
```python
# Check user IDs
async with AsyncSessionLocal() as s:
    users = await s.execute(select(User))
    for user in users.fetchall():
        print(f"ID {user.id}: {user.login}")

# Check demo data
async with AsyncSessionLocal() as s:
    notes = await s.execute(select(Note))
    print(f"Notes: {len(notes.fetchall())}")
``` 