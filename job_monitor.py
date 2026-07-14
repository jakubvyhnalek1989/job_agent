import os
import json
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


URL = "https://www.startupjobs.cz/nabidky/qa-engineer,scrum-master,tester"
STATE_FILE = "known_jobs.json"

EMAIL_TO = "jakubvyhnalek1989@gmail.com"
EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]


def load_old_jobs():
    if not os.path.exists(STATE_FILE):
        return set()

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))


def save_jobs(jobs):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(jobs), f, ensure_ascii=False, indent=2)


from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def get_jobs():

    jobs = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent="Mozilla/5.0"
        )

        page.goto(
            URL,
            wait_until="networkidle",
            timeout=60000
        )

        html = page.content()

        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    for link in soup.find_all("a", href=True):
        href = link["href"]

        if "/nabidka/" in href:
            if href.startswith("/"):
                href = "https://www.startupjobs.cz" + href

            jobs.add(href)

    print(f"Found jobs: {len(jobs)}")

    return jobs


def send_email(new_jobs):
    if not new_jobs:
        return

    body = "Nové pracovní nabídky:\n\n"

    for job in sorted(new_jobs):
        body += job + "\n"

    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = "Nové QA nabídky StartupJobs"

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)


def main():
    old_jobs = load_old_jobs()
    current_jobs = get_jobs()

    new_jobs = current_jobs - old_jobs

    if new_jobs:
        send_email(new_jobs)

    save_jobs(current_jobs)


if __name__ == "__main__":
    main()