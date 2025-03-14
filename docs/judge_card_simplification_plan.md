# Judge Card Simplification Plan

## Overview
This document outlines the plan to simplify the judge cards on the frontpage of the Judicial Accountability Initiative. The current display shows:

```
Judge Michael Brown
Tier: Federal District Court Judge
Position: Federal Judge
Ruling: Protected civil liberties
```

The simplified version will show:

```
Judge Name
Role: [Tier for federal judges] or [Tier (State Code) for state judges]
Ruling: [Ruling text]
```

## Implementation Plan

### 1. Database Changes

#### 1.1 Assess Current Schema
The current database schema for judges includes:
- `id` (SERIAL PRIMARY KEY)
- `name` (TEXT)
- `job_position` (TEXT)
- `ruling` (TEXT)
- `link` (TEXT)
- `x_link` (TEXT)
- `displayed` (INTEGER)
- `tier` (VARCHAR)
- `state` (VARCHAR)

No schema changes are needed as we'll be using the existing fields but displaying them differently.

### 2. Backend Changes

#### 2.1 Main App (`app.py`)
- Update the `/judges` endpoint to format the judge data appropriately
- Keep returning all fields to maintain backward compatibility
- No changes needed to the `submit_judge` endpoint as we'll continue storing the same data

#### 2.2 Admin App (`admin_app/app.py`)
- Update the judge display in the admin interface to match the new format
- Ensure that the admin app can still edit all fields

### 3. Frontend Changes

#### 3.1 Main App Frontend

##### 3.1.1 HTML Templates (`templates/index.html`)
- Update the judge card templates to reflect the new simplified format
- Remove the position field from the display
- Format the role field to show tier for federal judges or tier + state code for state judges

##### 3.1.2 JavaScript (`static/js/judges.js`)
- Update the `displayJudges` function to format the role field correctly
- Modify how the tier and state information is displayed
- Create a helper function to format the role based on tier and state

#### 3.2 Form Submission (`static/js/form.js`)
- Update the form to reflect the simplified display
- Keep collecting all the same data fields

#### 3.3 Admin App Frontend
- Update the admin templates to display judges with the new format
- Ensure all fields are still editable in the admin interface

### 4. Testing Plan

#### 4.1 Database Testing
- Verify that existing data is correctly displayed in the new format
- Test that new submissions are stored correctly

#### 4.2 Frontend Testing
- Test the display of federal judges (tier only)
- Test the display of state judges (tier + state code)
- Test the form submission process
- Test the admin interface for viewing and editing judges

### 5. Detailed Implementation Steps

#### 5.1 Backend Changes

1. **Main App (`app.py`):**
   - No changes needed to the database schema or data retrieval
   - The frontend will handle the display formatting

2. **Admin App (`admin_app/app.py`):**
   - No changes needed to the backend logic
   - Updates will be in the templates only

#### 5.2 Frontend Changes

1. **Update Judge Card Templates (`templates/index.html`):**
   - Modify the judge card templates to use the new format
   - Remove the separate position field
   - Update the tier/state display to use the new role format

2. **Update JavaScript Logic (`static/js/judges.js`):**
   - Create a helper function `formatJudgeRole(tier, state)` to format the role field
   - For federal judges: return the tier display name
   - For state judges: return `${tierDisplayName} (${stateCode})`
   - Update the card population logic to use this function

3. **Update Form Submission (`static/js/form.js`):**
   - Keep the form fields the same to maintain data collection
   - Update any display text to reflect the simplified format

4. **Update Admin Templates:**
   - Update the admin templates to display judges with the new format
   - Ensure all fields remain editable

### 6. Implementation Order

1. Create helper function in JavaScript to format the role field
2. Update the main app frontend templates
3. Update the main app JavaScript logic
4. Update the admin app templates
5. Test all changes thoroughly
6. Deploy the changes

### 7. Rollback Plan

If issues arise during implementation:

1. Revert the JavaScript changes
2. Revert the template changes
3. The database schema and data will remain unchanged, so no rollback needed there

### 8. Post-Implementation Verification

1. Verify that all judge cards display correctly on the frontpage
2. Verify that the admin app displays judges correctly
3. Verify that new submissions are processed correctly
4. Verify that voting functionality works correctly with the new display format