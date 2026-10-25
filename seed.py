import sqlite3
from pathlib import Path


DATABASE = Path(__file__).with_name("campuspath.db")

OPPORTUNITIES = [
    (
        "Undergraduate Tech Scholarship",
        "Example Foundation",
        "Scholarship",
        "Financial support for eligible undergraduate students in technology-related fields.",
        "2027-03-31",
        "https://example.com/scholarship",
    ),
    (
        "Student Web Development Internship",
        "Example Tech Company",
        "Internship",
        "A learning opportunity for students interested in web development.",
        "2027-04-15",
        "https://example.com/internship",
    ),
    (
        "National Student Innovation Challenge",
        "Example Innovation Hub",
        "Competition",
        "An opportunity for students to present innovative solutions to real problems.",
        "2027-05-20",
        "https://example.com/competition",
    ),
]

connection = sqlite3.connect(DATABASE)
try:
    connection.execute("PRAGMA foreign_keys = ON")
    existing_titles = {
        row[0]
        for row in connection.execute("SELECT title FROM opportunities")
    }
    new_opportunities = [
        opportunity
        for opportunity in OPPORTUNITIES
        if opportunity[0] not in existing_titles
    ]
    connection.executemany(
        """
        INSERT INTO opportunities
        (title, organization, category, description, deadline, application_url)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        new_opportunities,
    )
    connection.commit()
finally:
    connection.close()
