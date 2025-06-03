# KanMind Backend

![KanMind Logo](../frontend/assets/icons/logo_icon.svg)

This repository contains the Django REST Framework–based backend for KanMind, a simple kanban-like board manager.
Users can register, authenticate with token-based login, and then create/manage boards, tasks, and comments via a RESTful API.

---

## Features

- **User Registration & Login**  
  - Register a new account (username, email, password).  
  - Obtain a DRF Token upon login.

- **Email-Check**  
  - Verify if a given email belongs to a registered user.

- **Boards Management**  
  - Create new boards (owner automatically assigned).  
  - List all boards a user either owns or is a member of.  
  - View board details (including owner, members, tasks).  
  - Update board title & member list (add/remove members).  
  - Delete a board (only owner can delete).

- **Tasks Management**  
  - Create tasks under a specific board (must be a board member).  
  - List all tasks that the user is involved with (owner, member, assignee, or reviewer).  
  - View, update, or delete a specific task (only allowed if user is board owner or member).  
  - Each task contains: title, description, status (`to-do` / `in-progress` / `review` / `done`), priority (`low` / `medium` / `high`), assignee, reviewer, due date, and comment count.

- **Comments on Tasks**  
  - List all comments on a given task (must be a board member to view).  
  - Create a new comment on a task (author is automatically set from the authenticated user).  
  - Delete a comment (only the comment’s author can delete).

---