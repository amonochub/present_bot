# Tour Feature Documentation

## Overview
The tour feature provides a guided demonstration of all 6 roles in the SchoolBot system. It allows demo account users to cycle through each role, see their main menu, and understand their functionality.

## Implementation Details

### Files Modified/Created:
1. **`app/handlers/tour.py`** - Main tour handler with FSM states
2. **`app/keyboards/main_menu.py`** - Added BACK_BTN for navigation
3. **`app/bot.py`** - Included tour router
4. **`app/i18n/ru.toml`** - Added help text for super role
5. **`tests/test_basic.py`** - Added test for tour text mapping

### Key Components:

#### FSM States
- `TourFSM.step` - Manages the current step in the tour

#### Tour Roles Order
```python
TOUR_ROLES = ["teacher", "admin", "director", "student", "parent", "psych"]
```

#### Role Descriptions
Each role has a descriptive text explaining their main functionality:
- **Teacher**: Adds notes, IT tickets, media center requests
- **Admin**: Ticket kanban, mass broadcasts to teachers
- **Director**: Views KPI, gives assignments
- **Student**: Views assignments, can ask teacher questions
- **Parent**: Orders PDF certificates, monitors assignments
- **Psychologist**: Receives requests, marks as "Resolved"

## Usage

### For Demo Account Users:
1. Login with demo credentials (demo01/demo)
2. Type `/tour` to start the tour
3. Each step shows:
   - Role description with emoji and HTML formatting
   - Role-specific main menu
   - "Next →" button to continue
   - "◀️ Main Menu" button to exit tour
4. After completing all 6 roles, returns to demo menu

### Navigation:
- **"➡️ Дальше"** - Continue to next role
- **"◀️ Главное меню"** - Exit tour and return to demo menu
- **Role menu buttons** - Interact with current role's features

## Technical Features

### State Management
- Uses FSM to track current tour step
- Automatically clears state when tour completes or user exits
- Can restart tour at any time

### Role Switching
- Uses same `set_role()` function as regular role switching
- Maintains consistency with existing role management
- Doesn't interfere with real user scenarios

### UX Considerations
- Tour can be exited at any time
- FSM state clears when user exits
- Tour can be restarted from demo menu
- All role menus remain functional during tour

## Testing

### Manual Testing Steps:
1. Login as demo01/demo
2. Execute `/tour`
3. Verify each role shows correct description and menu
4. Test "Next →" button progression
5. Test "◀️ Main Menu" exit functionality
6. Verify tour completion message
7. Test restarting tour from demo menu

### Automated Testing:
- `test_tour_text_mapping()` - Verifies all role descriptions exist and are properly formatted

## Future Enhancements
- Add tour progress indicator (e.g., "Step 2 of 6")
- Add role-specific demo actions
- Add tour completion statistics
- Add multi-language support for tour descriptions
