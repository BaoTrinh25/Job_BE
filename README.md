Key Features
For Job Seekers
Registration and Login: Standard sign-up/login with Google OAuth integration.
Job Search: Comprehensive job search with filters.
Job Applications: Apply for job postings and track application status.
Feedback and Comments: Leave ratings and comments on job postings.
Favorite Jobs: Save preferred jobs for later.
Messaging: Real-time messaging with employers via WebSocket.
Application Management: View and manage the list of applied jobs.
Account Management: Disable account, update profile, and candidate information.
For Employers
Registration and Login: Sign-up and login capabilities.
Job Posting: Create, update, hide, or delete job listings.
Subscription Packages: Purchase posting packages with online payment via Stripe.
Messaging: Real-time chat with job seekers.
Applicant Management: Accept or reject applicants, with email notifications sent to candidates.
Account Management: Disable account, update profile, and company information.
Technology Stack
Backend Framework: Python, Django Rest Framework
Real-Time Communication: WebSocket
Authentication: OAuth2 (including Google OAuth)
Database: MySQL, Redis (for caching)
Deployment: Docker
Getting Started
To run this project locally, follow these steps:

Clone the Repository:

bash
Sao chép mã
git clone https://github.com/BaoTrinh25/JOB_BE.git
cd JOB_BE
Set Up Environment Variables: Create a .env file and add the required configurations for MySQL, Redis, and OAuth credentials.

Run Docker Compose: Ensure Docker is installed on your machine. Then start the services:

bash
Sao chép mã
docker-compose up --build
Access the API: Once Docker starts, the API is accessible at http://localhost:<PORT>/api.
