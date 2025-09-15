from setuptools import setup, find_packages

setup(
    name="meeting-scheduler-bot",
    version="1.0.0",
    description="Conversational AI bot for automated meeting scheduling with Google Calendar",
    packages=find_packages(),
    install_requires=[
        "google-api-python-client==2.108.0",
        "google-auth-httplib2==0.1.1",
        "google-auth-oauthlib==1.1.0",
        "google-generativeai==0.3.2",
        "python-dateutil==2.8.2",
        "pytz==2023.3",
        "colorama==0.4.6",
        "python-dotenv==1.0.0",
    ],
    python_requires=">=3.8",
)
