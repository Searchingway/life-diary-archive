Design a complete high-fidelity desktop UI system for a local-first personal life archive app called “人生档案 Diary”.

This is a desktop productivity app, not a landing page and not a mobile app.

Frame size:
Design for a desktop window around 1440×900 or 1500×900.

Product positioning:
“人生档案 Diary” is a local-first personal archive and planning workspace.
The mobile app is for quick daily capture.
The desktop app is for importing, organizing, analyzing, reviewing, archiving, and planning.
All data is stored locally. There is no cloud sync, no account login, and no social feed.
AI is an assistant only. AI can generate drafts, but the user must preview and confirm before applying. AI must not directly overwrite user records.

Main user goals:

1. Write daily diary entries.
2. Browse places and footprints.
3. Record light plans.
4. Turn light plans into action plans.
5. Organize thoughts.
6. Evaluate time, money, energy, emotion, risk, and opportunity cost.
7. Store important info such as freelance orders, courses, links, contacts, and local folders.
8. Record self observations.
9. Write lessons and reflections.
10. Write deeper self analysis.
11. Record works/media reflections.
12. Manage data backup, restore, import/export, and AI settings.

Important design principle:
Separate “viewing”, “editing”, and “executing”.
Do not put every field directly on the main page.
The main page should be for viewing, writing, or executing.
Creation and editing can use modals, side panels, or dedicated edit states.
Avoid dense database-like forms.

Navigation:
Design a desktop-style navigation structure with grouped modules.

Suggested groups:

1. Overview

   * Dashboard

2. Daily Records

   * Diary
   * Footprints
   * Self Observation

3. Thinking & Reflection

   * Light Thought
   * Light Resource
   * Lessons & Reflection
   * Self Analysis

4. Plans & Execution

   * Light Plan
   * Action Plan

5. Information & Works

   * Info Memo
   * Works / Media Reflection

6. System

   * Data Management
   * AI Settings

You may use a left sidebar, a hybrid sidebar, or another clear desktop navigation pattern, but do not make the navigation crowded like many top tabs.

Create high-fidelity designs for all screens below.

SCREEN 1: Dashboard / 总览工作台

Purpose:
When the user opens the app, they should know what needs attention today, what has been recorded recently, and what they can continue working on.

Must include:

* Header: “人生档案工作台”
* Today’s date
* Local data status
* Quick actions:

  * Write Diary
  * New Info Memo
  * New Light Plan
  * AI Breakdown
  * Backup Data
* Today’s tasks
* In-progress action plans
* Recent timeline across all modules
* Recent diary
* Recent info memos
* Recent thoughts/reflections
* Monthly diary count
* Monthly word count
* Module overview

The dashboard should feel like a control center, not a plain statistics table.

SCREEN 2: Diary / 日记

Purpose:
A writing-first page.

Layout:

* Left area: diary list, search, new diary button, date filter.
* Main area: large writing editor.
* Top of main area: date, title, save status, save button.
* Secondary area: collapsible images, related footprints, export Word/PDF, heatmap/statistics.

Important:
The diary body is the main character.
Images, heatmap, export, and related footprints are secondary.
Do not let statistics or image management take space away from writing.

Create states:

* Empty diary list state.
* Viewing an existing diary.
* Editing a diary.
* Images collapsed.
* Images expanded.

SCREEN 3: Footprints / 足迹

Purpose:
Represent the two-level structure:
Place archive → multiple dated visit records.

Layout:

* Left area: place list, search, new place.
* Main top: selected place archive, place summary, place images.
* Main middle: visit timeline under this place.
* Main bottom or side panel: selected visit detail.

Must include:

* Place title
* Place description
* Visit date
* Visit reflection
* Visit images
* Button to open diary of the same date

Important:
Do not design it as one flat form.
The page must clearly show “place” and “dated visits” as two levels.

SCREEN 4: Light Plan / 轻计划

Purpose:
Low-pressure plan capture.
It is for quick “I want to do this” or “I want to stop doing this”.

Must support:

* Additive plan
* Subtractive plan

Layout:

* Left list: plan list, search, filter by all/additive/subtractive/status.
* Main area: selected plan detail.
* Main actions:

  * New Plan
  * Mark Complete
  * AI Complete Plan
  * Convert to Action Plan

For subtractive plan, include:

* Trigger scene
* Behavior to avoid
* Reason
* Replacement behavior

Important:
Keep this page light.
Do not make it a full project management page.
The action plan page handles execution.

SCREEN 5: Action Plan / 行动计划

Purpose:
Convert light plans into dated executable tasks.
This is an execution workspace, not a CRUD form.

Overall layout:

* Left area: action plan list, search, status filter.
* Main header: selected plan title, date range, progress, status, AI breakdown, edit plan.
* Main content: view switcher between Timetable and Task Chain.

Timetable view:

* Group tasks by date.
* Each date section contains task cards.
* Each task card includes:

  * checkbox / completion state
  * task title
  * estimated time
  * note
  * status
* Completed tasks should look different.
* Today’s tasks should be emphasized.

Task Chain view:

* Use a dark canvas-like area.
* Each day is a vertical chain.
* Tasks are circular nodes on the chain.
* Nodes are connected by lines.
* Completed nodes are highlighted or checked.
* Selecting a node opens a task detail panel.
* The visual should feel like a task map / skill tree / progress chain.

Create/edit behavior:

* Creating or editing a plan should use a modal or side panel.
* Creating or editing a task should use a modal or side panel.
* Do not place the full creation form directly on the main execution screen.

AI behavior:

* “AI Breakdown” opens a preview flow.
* User selects a light plan.
* AI generates dated tasks.
* User previews.
* User confirms.
* Tasks are created.
* AI never directly overwrites existing data.

SCREEN 6: Light Thought / 轻思考

Purpose:
Capture questions that are not clear yet and gradually organize them.

Layout:

* Left area: thought list, search, status filter.
* Main area:

  * Question title
  * Problem description
  * Thought entries by date
  * Current conclusion
  * Next action
* Actions:

  * New Thought
  * Add Thought Entry
  * AI Organize Thought
  * Convert to Light Plan

Important:
This page is for thinking through uncertainty.
It should not look like a long static article.
Thought entries should look like a progressive thinking timeline.

SCREEN 7: Light Resource / 轻资源

Purpose:
Evaluate what a decision consumes: time, money, energy, emotion, courage, body, attention, risk, opportunity cost.

Layout:

* Left area: resource topic list, search, type filter.
* Main area:

  * Topic title
  * Description
  * Resource cost cards:

    * Time
    * Money
    * Energy
    * Emotion
    * Courage
    * Body
    * Attention
    * Risk
    * Opportunity cost
  * Repetition / eternal return test:
    “If this repeats 10 times, would I still choose it?”
  * Overall judgment
* Actions:

  * New Resource
  * AI Evaluate Resource
  * Convert to Light Plan
  * Copy as Lesson

Important:
Do not design it as a budgeting spreadsheet.
It is a judgment and decision page.

SCREEN 8: Info Memo / 信息备忘

Purpose:
Manage important information that is easy to forget:
freelance orders, online courses, links, contacts, websites, local folders, project notes.

Layout:

* Left area: search, type filter, status filter, memo list.
* Main area: display-style detail view, not a huge form.
* Cards:

  * Basic information
  * Customer / source information
  * Money information
  * Time and deadline
  * Deliverables
  * Links and local path
  * Notes

Info types:

1. Freelance Order
   Fields:

   * customer
   * intermediary
   * executor
   * order date
   * deadline
   * duration days
   * price
   * deposit
   * final payment
   * deliverables
   * related link
   * local folder path
   * notes

2. Online Course
   Fields:

   * course name
   * platform
   * course link
   * learning direction
   * paid status
   * progress
   * reason

3. General Info
   Fields:

   * category
   * source
   * link
   * content
   * reminder date
   * note

Money section:
Price, Deposit, Final Payment should be visually separated as three clear money cards, not tiny crowded inputs.

Create/edit should use modal or side panel.

SCREEN 9: Self Observation / 自我观察

Purpose:
Quickly record current emotional and physical state.
This is not a psychological diagnosis tool.

Layout:

* Left area: date list, emotion filter, intensity filter.
* Main area:

  * timestamp shown as “yyyy-MM-dd HH:mm”
  * emotion
  * intensity
  * current need
  * trigger
  * body feeling
  * notes
* Actions:

  * New Observation
  * Convert to Self Analysis

Important:
This should feel lightweight.
Do not make it look like a clinical form.
Do not show long ISO timestamps.

SCREEN 10: Lessons & Reflection / 教训与反思

Purpose:
Record events, bad decisions, project mistakes, emotional lessons, and what to do differently next time.

Layout:

* Left area: reflection list, search, event type filter, severity filter.
* Main area:

  * title
  * event type
  * severity
  * tags
  * linked diary entries
  * structured writing sections:

    * What happened
    * What I thought then
    * Result
    * Mistake in judgment
    * Real problem
    * Cost
    * Next strategy
    * One-sentence lesson
* Actions:

  * New Reflection
  * Link Diary
  * Add Images

Important:
This is a structured review page.
It should support long writing, but sections should be visually separated.

SCREEN 11: Self Analysis / 自我分析

Purpose:
Deep personal writing and reflection around emotion, dreams, relationships, desire, repetition patterns, body feelings, freelance anxiety, and learning difficulties.

Layout:

* Left area: analysis list, search, analysis type filter.
* Main area:

  * title
  * analysis type
  * tags
  * linked diary
  * linked lesson
  * large structured writing sections:

    * Trigger event
    * Emotion at the time
    * Body reaction
    * Surface thought
    * Real fear
    * Real desire
    * Repetition pattern
    * Imagined evaluation by others
    * Defense method
    * Similar past experience
    * What I noticed
    * Next action
* Actions:

  * New Analysis
  * Link Diary
  * Link Lesson
  * Add Images

Important:
This page should feel like a deep writing page.
The writing sections should be comfortable and spacious.

SCREEN 12: Works / Media Reflection / 作品感悟

Purpose:
Record how books, films, anime, games, articles, courses, and videos affect the user.

It is not Douban, Steam, IMDb, or a media database.
The main point is personal reflection.

Layout:

* Left area: works list, search, work type filter, status filter.
* Main area:

  * work title
  * work type
  * creator
  * status
  * start date
  * finish date
  * rating
  * tags
  * main reflection area: “My Reflection”
  * collapsible quote/excerpt area
  * linked diary
  * linked self analysis
  * images/posters

Important:
“My Reflection” must be the largest writing area.
Quotes/excerpts should be secondary and collapsible.

SCREEN 13: Data Management / 数据管理

Purpose:
Safe local data management.

Layout:

* Sections:

  * Data location
  * Backup
  * Restore
  * Import mobile ZIP
  * Export desktop ZIP
  * Open data folder
  * Module statistics
  * Health check
  * Logs
* Show clear warnings before destructive operations.
* Import mobile ZIP should explain:

  * It reads manifest.json.
  * It automatically backs up current data first.
  * It merges by id instead of overwriting the whole dataset.

Important:
This page should be utilitarian and safe.
Do not make it decorative.

SCREEN 14: AI Settings / AI 设置

Purpose:
Configure DeepSeek API safely.

Layout:

* Enable AI toggle
* API Key input, masked by default
* Base URL
* Model name
* Timeout seconds
* Test connection
* Save settings

Rules:

* Do not show full API key.
* Do not log full API key.
* Show clear error state if API key is missing or invalid.

SCREEN 15: AI Preview Dialog / AI 预览弹窗

Purpose:
All AI-generated content must be previewed before applying.

Layout:

* Modal dialog.
* Left panel: original user content.
* Right panel: AI-generated draft.
* Bottom actions:

  * Regenerate
  * Copy
  * Apply
  * Cancel

Rules:

* Explain which fields will be changed before applying.
* AI must not directly save or overwrite data.
* The user confirms before applying.

SCREEN 16: Create / Edit Modal Pattern

Create a reusable modal design pattern for:

* New Diary metadata
* New Place
* New Visit
* New Light Plan
* New Action Plan
* New Action Task
* New Info Memo
* New Reflection
* New Self Analysis
* New Work Reflection

Modal structure:

* Header: action title
* Body: form fields grouped logically
* Footer:

  * Cancel
  * Save
  * Save and Continue if appropriate

The modal should not be too wide.
Use clear sections.
Do not create dense full-page forms.

Global design requirements:

* This is a desktop app for long-term daily use.
* Prioritize readability, writing comfort, and information hierarchy.
* Separate viewing, editing, and execution.
* Use cards to group related information.
* Use spacious writing areas for diary, reflections, self analysis, and work reflection.
* Avoid nested group boxes.
* Avoid dense form pages.
* Avoid making everything look like a database editor.
* Avoid excessive green buttons.
* Avoid decorative illustrations that waste space.
* Avoid SaaS landing page style.
* Avoid mobile-first layouts.

Deliverables:
Generate a complete desktop UI design system and all screens listed above.
Include:

1. Navigation structure.
2. Dashboard.
3. Diary.
4. Footprints.
5. Light Plan.
6. Action Plan with both Timetable and Task Chain view.
7. Light Thought.
8. Light Resource.
9. Info Memo.
10. Self Observation.
11. Lessons & Reflection.
12. Self Analysis.
13. Works / Media Reflection.
14. Data Management.
15. AI Settings.
16. AI Preview Dialog.
17. Generic Create/Edit Modal pattern.

The result should be detailed enough for a developer to implement later in Python/PySide6 or another desktop UI framework.
