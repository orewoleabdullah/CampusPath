# CampusPath
**Video Demo:** [Add your video link here]

## Description
CampusPath is a web application designed to help university students discover and manage opportunities such as scholarships, internships, competitions, and fellowships. Students can browse available opportunities, search by title, filter by category, save opportunities they are interested in, and track their application progress.

The project addresses a common challenge faced by students: keeping track of opportunities, their deadlines, and the status of applications. CampusPath brings these activities into one place so students can organise their search and follow up on opportunities more easily.

## Features

- **User registration and login:** Students can create accounts and log in securely.
- **Opportunity discovery:** Browse opportunities listed on the platform.
- **Search and filtering:** Find opportunities by title and category.
- **Saved opportunities:** Save listings to a personal dashboard and remove them when no longer needed.
- **Application tracking:** Update the status of saved opportunities, including marking them as applied.
- **Deadline information:** View deadline indicators that help users identify approaching or passed deadlines.
- **Administration:** Authorised administrators can create, edit, publish, unpublish, and delete opportunity listings.
- **Security:** Passwords are stored as hashes, and the application includes session protections and CSRF checks for POST requests.

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- `python-dotenv`

## Project Files

- `app.py` contains the Flask application, routes, authentication logic, database operations, administrator functions, and request protections.
- `schema.sql` defines the database tables for users, opportunities, and saved opportunities.
- `seed.py` adds sample opportunity records to the database.
- `requirements.txt` lists the Python dependencies required to run the application.
- `.gitignore` specifies local files and directories that should not be committed to version control, including environment secrets, the virtual environment, and the local database.
- `.env` stores local environment configuration, including the Flask secret key. It is not committed to version control.
- `templates/index.html` displays the opportunity listing and search interface.
- `templates/register.html` contains the registration page.
- `templates/login.html` contains the login page.
- `templates/dashboard.html` displays a student's saved opportunities and application statuses.
- `templates/admin.html` provides the administrator's opportunity management interface.
- `templates/admin_opportunity_form.html` contains the form for creating or editing an opportunity.
- `static/style.css` contains the application's visual styling.
- `static/script.js` contains client-side JavaScript.
- `campuspath.db` is the local SQLite database created and used by the application. It is excluded from version control.

## Design Choices
Flask was selected because it supports a lightweight Python web application while making it possible to implement routing, authentication, and database operations clearly. SQLite provides a simple relational database suitable for a student project without requiring a separate database server.

The database separates users, opportunities, and saved opportunities. The saved-opportunities table connects students to listings and stores their application statuses. This design allows multiple students to track the same opportunity independently.

Administrator access is separate from ordinary student access. This allows authorised users to manage listings without exposing administrative functions to every registered user. Opportunity publication status also makes it possible to prepare a listing before making it visible to students.

The application uses password hashing instead of storing plain-text passwords. It also uses a secret key loaded from local environment configuration and includes CSRF protection for POST requests.

## Setup and Usage

### Prerequisites

- Python 3.10 or later
- Git (if cloning the repository)

### Installation

1. Clone the repository or download the project files.
2. Open a terminal in the project directory.
3. Create a virtual environment:

```
python -m venv venv
```

4. Activate the virtual environment.

On Windows PowerShell:

```
.\venv\Scripts\Activate.ps1
```

On macOS or Linux:

```
source venv/bin/activate
```

5. Install the dependencies:

```
pip install -r requirements.txt
```

6. Create a `.env` file in the project root and set a securely generated Flask secret key:

```
SECRET_KEY=replace_with_your_own_random_secret
```

Replace the example value with a randomly generated secret. Do not commit `.env` to version control.

### Running the Application

Start the development server with:

```
flask --app app run --debug
```

Open the local address displayed in the terminal in your browser.

The application initializes its SQLite database automatically when it starts. Register an account to explore the student features.

### Administrator Access

Administrator access must be granted from the project environment to an existing user. Run:

```
flask --app app promote-admin YOUR_USERNAME
```

Replace `YOUR_USERNAME` with the username of the account to promote. Only use this command in a trusted development environment.

### Important Notes

The application is intended for development and demonstration. The included sample opportunities use placeholder information and should be replaced with verified listings before public use. Do not use Flask's debug mode for a production deployment.

## Limitations and Future Improvements
The current version uses sample opportunity listings for demonstration. Before public deployment, these should be replaced with verified opportunities and accurate application links. Future improvements could include automated opportunity updates, email deadline reminders, stronger deployment configuration, and additional accessibility testing.

## AI Assistance Disclosure
AI tools were used to assist with reviewing, debugging, and refining parts of this project. The project author is responsible for reviewing, testing, understanding, and maintaining the submitted code.
