# Date Operators Implementation TODO

This document outlines all possible date operators for smart folder rules, organized by priority and implementation complexity.

## Current Implementation Status

### ✅ Already Implemented
- `is_null` - Date field is empty
- `is_not_null` - Date field has a value
- `is_today` - Date falls within today
- `on` - Exact date match (requires ISO date)
- `before` - Before specific date (requires ISO date)
- `after` - After specific date (requires ISO date)
- `between` - Between two dates (requires 2 ISO dates)

## Phase 1: Critical Task Management Essentials 🚨

These are absolutely essential for any task management system and should be implemented first.

### Overdue Detection (Critical)
- [ ] `is_overdue` - Due date is in the past (due_at < today)
- [ ] `overdue_by_days` - Overdue by exactly N days
- [ ] `overdue_by_more_than` - Overdue by more than N days
- [ ] `overdue_by_less_than` - Overdue by less than N days

**Use Cases:**
- "Show me all overdue tasks"
- "Tasks overdue by more than 3 days"
- "Recently overdue items (less than 2 days)"

### Upcoming/Due Soon (Critical)
- [ ] `due_in_days` - Due in exactly N days
- [ ] `due_within_days` - Due within next N days
- [ ] `due_in_more_than_days` - Due more than N days from now

**Use Cases:**
- "Tasks due within next 3 days"
- "Tasks due exactly tomorrow"
- "Long-term tasks (due in more than 30 days)"

## Phase 2: Essential Relative Date Ranges 📅

Common relative date operations that users expect in modern applications.

### Past Ranges
- [ ] `within_last_days` - Date within last N days (includes today)
- [ ] `more_than_days_ago` - Date more than N days ago
- [ ] `exactly_days_ago` - Date exactly N days ago

**Use Cases:**
- "Tasks created in the last 7 days"
- "Tasks not touched in more than 30 days"
- "Tasks due exactly 5 days ago"

### Future Ranges
- [ ] `within_next_days` - Date within next N days (includes today)
- [ ] `starts_within_days` - Start date within next N days
- [ ] `starts_in_more_than_days` - Start date more than N days from now

**Use Cases:**
- "Tasks that can start within next 5 days"
- "Tasks starting more than 2 weeks from now"

## Phase 3: Calendar Period Support 📆

Standard calendar periods that align with how people think about time.

### Week-Based
- [ ] `this_week` - Current calendar week (Monday to Sunday)
- [ ] `next_week` - Next calendar week
- [ ] `last_week` - Previous calendar week
- [ ] `within_next_weeks` - Within next N weeks

**Use Cases:**
- "Tasks due this week"
- "Weekly planning view"
- "Tasks due within next 2 weeks"

### Month-Based
- [ ] `this_month` - Current calendar month
- [ ] `next_month` - Next calendar month
- [ ] `last_month` - Previous calendar month
- [ ] `within_next_months` - Within next N months

**Use Cases:**
- "Monthly goals and deadlines"
- "Quarterly planning"

### Today Variations
- [ ] `yesterday` - Date was yesterday
- [ ] `tomorrow` - Date is tomorrow
- [ ] `day_before_yesterday` - Date was day before yesterday
- [ ] `day_after_tomorrow` - Date is day after tomorrow

## Phase 4: Business Logic Support 💼

Business-aware date operations that account for work schedules.

### Business Days
- [ ] `next_business_day` - Next weekday (Monday-Friday)
- [ ] `last_business_day` - Previous weekday
- [ ] `business_days_from_today` - N business days from today (skip weekends)
- [ ] `business_days_ago` - N business days ago (skip weekends)

**Use Cases:**
- "Due next business day"
- "Tasks due in 3 business days"
- "Follow-up needed 5 business days ago"

### Weekend/Weekday Logic
- [ ] `this_weekend` - This Saturday or Sunday
- [ ] `next_weekend` - Next Saturday or Sunday
- [ ] `weekdays_only` - Only Monday-Friday dates
- [ ] `weekends_only` - Only Saturday-Sunday dates

**Use Cases:**
- "Personal tasks for this weekend"
- "Work tasks for weekdays only"

## Phase 5: Fuzzy/Human-Friendly Concepts 🧠

Human-friendly time concepts that make the system more intuitive.

### Fuzzy Time Ranges
- [ ] `soon` - Within next 3-7 days (configurable)
- [ ] `later` - More than 2-4 weeks from now (configurable)
- [ ] `recently` - Within last 3-7 days (configurable)
- [ ] `long_ago` - More than 30+ days ago (configurable)
- [ ] `very_soon` - Within next 1-2 days (configurable)

**Use Cases:**
- "Tasks due soon"
- "Things I can do later"
- "Recently completed items"

### Contextual Intelligence
- [ ] `urgent_overdue` - Overdue by more than 7 days (configurable)
- [ ] `mildly_overdue` - Overdue by 1-3 days (configurable)
- [ ] `approaching_deadline` - Due within 1-2 days (configurable)
- [ ] `long_term_goal` - Due more than 90 days from now (configurable)

**Use Cases:**
- "Urgent attention needed"
- "Mild priority items"
- "Long-term planning"

## Phase 6: Advanced Features 🚀

Advanced operators for power users and complex scenarios.

### Negation Operators
- [ ] `not_overdue` - Not overdue (due_at >= today or null)
- [ ] `not_due_today` - Not due today
- [ ] `not_this_week` - Not in current week
- [ ] `not_within_days` - Not within N days

**Use Cases:**
- "Tasks that are not overdue"
- "Non-urgent items"
- "Filter out this week's tasks"

### Compound Logic
- [ ] `overdue_or_due_today` - Overdue OR due today
- [ ] `due_this_week_or_overdue` - Due this week OR overdue
- [ ] `workdays_in_next_week` - Weekdays in next calendar week

**Use Cases:**
- "Action required items"
- "This week's focus plus catch-up"

### Seasonal/Quarterly
- [ ] `this_quarter` - Current business quarter
- [ ] `next_quarter` - Next business quarter
- [ ] `this_year` - Current calendar year
- [ ] `next_year` - Next calendar year

**Use Cases:**
- "Quarterly goals"
- "Annual planning"

## Implementation Considerations

### Technical Requirements
1. **Timezone Handling**: All relative dates should respect user's timezone
2. **Boundary Clarity**: Document inclusive/exclusive behavior for each operator
3. **Configurability**: Fuzzy operators should have configurable ranges
4. **Performance**: Ensure date calculations don't impact query performance
5. **Validation**: Proper input validation for day/week/month values

### Naming Conventions
- Use consistent naming patterns
- Prefer clarity over brevity
- Follow existing operator naming style
- Document all boundary behaviors

### User Interface Implications
Each new operator needs:
- [ ] UI input controls (number inputs, dropdowns)
- [ ] Help text and examples
- [ ] Validation messages
- [ ] Preview functionality

## Priority Recommendation

**Phase 1** (Critical): Implement immediately - core task management needs
**Phase 2** (Essential): Implement soon - common user expectations  
**Phase 3** (Important): Implement after core features - calendar integration
**Phase 4** (Useful): Implement for business users - work-focused features
**Phase 5** (Nice): Implement for UX polish - human-friendly concepts
**Phase 6** (Advanced): Implement for power users - complex scenarios

---

*This document should be reviewed and prioritized based on actual user feedback and usage patterns.*