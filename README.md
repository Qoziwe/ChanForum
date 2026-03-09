# ChanForum

ChanForum is a web-based community platform built from the ground up with Python, Flask, and SQLite. It serves as a digital gathering place for individuals to connect, share their ideas, and find like-minded people. 

## Ideology

At its core, **ChanForum** was created to prioritize **simplicity, speed, and genuine connection** over algorithmic feeds and complex abstractions. The platform is designed without barriers, providing a straightforward way for users to broadcast their thoughts through posts and pictures, naturally discovering friends and establishing networks. It aims to emulate the classic, tight-knit feeling of early internet forums and imageboards, adapted for modern usability.

## Capabilities & Features

ChanForum provides a rich set of capabilities out of the box aimed at maximizing user interaction:

### 👤 Profile & Identity
- **Account Creation:** Securely register and log in to your personal account via an email and password interface.
- **Customization:** Upload and update custom profile pictures (avatars) to express your digital identity.
- **Self Expression:** Dedicated user profile pages to view someone's basic information and content.
- **Public vs Private:** Unauthenticated users are appropriately restricted from participating but can still browse public posts.

### 📝 Content Creation
- **Rich Posting:** Create structured posts with a Title, Description, and detailed Content text.
- **Image Sharing:** Easily upload image attachments directly into your posts.
- **Content Control:** Modify or completely delete your own posts at any time.

### 💬 Social Interactions
- **Global Feed:** Scroll through a chronologically ordered feed of all community posts on the main page.
- **Likes System:** Upvote/Like posts to show appreciation. The system prevents double-liking and tracks total engagement.
- **Comments:** Participate in discussions by leaving comments under any post. The comment section acts as a direct line of communication with the post author and other readers.

### 🤝 Networking
- **Friends System:** Send connection requests to other users whose content you enjoy by adding them to your Friend List.
- **Friend Management:** Access a dedicated "Friends" page (`/friends`) to view and manage all users you are connected to.
- **Author Discovery:** Click on a post's author to view their unique profile (`/unknownuser/`) and instantly add them to your network.

## Technology Stack

- **Backend:** Python, Flask (Web Framework)
- **Database:** SQLite3
- **Frontend:** HTML, CSS, JavaScript (Jinja2 Templates)

## Project Structure

```text
ChanForum/
│
├── app.py                  # Main Flask application file containing all backend routes and logic
├── database_sqlite.py      # Script for initializing the database schema
├── scheme.sql              # SQL schema definition for the initial database setup
├── requirements.txt        # Python dependencies required to run the application
│
├── db/                     # Directory for SQLite database files
│   ├── databasepost.db     # Stores posts, comments, and likes
│   └── databaseusers.db    # Stores user credentials, profiles, and friend lists
│
├── static/                 # Static assets directly served to the client
│   ├── styles/             # CSS stylesheets for the UI
│   ├── scripts/            # Client-side JavaScript
│   ├── images/             # Static images
│   └── fonts/              # Custom fonts
│
└── templates/              # Jinja2 HTML templates
    ├── base.html           # Base template with common layout (navbar, structure, etc.)
    ├── mainpage.html       # Main feed for displaying all posts
    ├── login.html          # User login page
    ├── register.html       # User registration page
    ├── profile.html        # Current user logged-in profile page
    ├── update_profile.html # Page to edit profile info and avatar
    ├── create.html         # Page to create a new post
    ├── edit.html           # Page to edit an existing post
    ├── post.html           # Individual post view with comments
    ├── friends.html        # List of the user's friends
    ├── userpost.html       # List of posts created by the logged-in user
    ├── unknownprofile.html # View for another user's profile
    └── unknownuser.html    # View for adding a post author as a friend
```

## Setup & Installation

Follow these steps to set up and run the application locally:

### 1. Prerequisites

Ensure you have Python 3.x installed on your machine.

### 2. Clone the repository

```bash
git clone <repository_url>
cd ChanForum/ChanForum
```

*(If the project isn't using git yet, simply navigate to the `ChanForum` directory).*

### 3. Install Dependencies

You can install the required packages using pip:

```bash
pip install -r requirements.txt
```

*Note: It is recommended to use a virtual environment (`venv`).*

### 4. Run the Application

Start the Flask development server:

```bash
python app.py
```

The application will start running on port `1488`. You can access it in your web browser at:
`http://127.0.0.1:1488`

## Database Architecture

The application uses multiple SQLite databases for storing specific data:

- **Users (`databaseusers.db`):** Contains the `users` table including `id`, `username`, `email`, `password`, `profile_image` (BLOB), `uniq_id` (hashed username context), and `friend_id` (comma-separated list of friend identifiers).
- **Posts (`databasepost.db`):** 
  - `posts`: Stores the `id`, `title`, `content`, `description`, `post_image` (BLOB), `author`, `user_uniq_id`, and timestamps.
  - `post_likes`: Tracks which users liked which posts.
  - `comments`: Stores comments linked to specific posts and their authors.

## Future Improvements

- Switch plain-text password storage to hashed keys (e.g., using `werkzeug.security`).
- Enhance the SQLite database structure (e.g., using foreign keys strictly, or migrating to a more robust DB like PostgreSQL for production instead of multiple SQLite files).
- Refactor the friend association mapping from comma-separated string `friend_id` to a normalized many-to-many junction table.
