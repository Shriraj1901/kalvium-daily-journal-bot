"""
Daily Google Form submitter for the Kalvium Simulated Work journal.
Reuses a saved logged-in session (auth_state.json) so no credentials are
stored anywhere. Selects "working day, present" and fills the four
follow-up questions with varied, generated content each run.
"""
import random
import sys
from playwright.sync_api import sync_playwright

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSc8RRUAG8n8nPB9dm21m_MxwHQ-JuDnEj7GnvwEkWXykkKFuQ/viewform"

TASKS = [
    "reviewing the onboarding module requirements",
    "implementing form validation logic for the sign-up flow",
    "refactoring the authentication middleware",
    "writing unit tests for the payment processing module",
    "debugging a state synchronization issue in the dashboard",
    "optimizing a slow SQL query on the orders table",
    "building a reusable component for the notifications panel",
    "setting up CI checks for the pull request pipeline",
    "pairing with a teammate on the API rate-limiting feature",
    "documenting the internal API endpoints",
    "exploring Docker basics for local environment setup",
    "practicing a data structures and algorithms kata",
    "attending a mentor session on system design fundamentals",
    "cleaning up technical debt in the utils module",
    "investigating a flaky test in the CI suite",
    "improving error handling in the file upload service",
    "working through a React state management exercise",
    "reviewing a teammate's pull request",
    "sketching out the schema for a new feature",
    "reading through the style guide and applying it to recent code",
]

CHALLENGES_SOLVED = [
    "figured out why an API call was returning stale data by fixing a caching bug",
    "resolved a merge conflict that was blocking the feature branch",
    "tracked down a null reference issue in a form submission handler",
    "fixed a CSS layout bug that broke on smaller screens",
    "got a failing test suite passing by correcting a mocked dependency",
    "identified the root cause of a memory leak in a long-running process",
    "worked out a tricky edge case in some input validation logic",
    "resolved a race condition in an async function",
    "corrected a misconfigured environment variable that was breaking the build",
    "found and fixed an off-by-one error in a pagination function",
]

CHALLENGES_PENDING = [
    "a performance bottleneck in a search feature that needs more profiling",
    "an intermittent test failure that hasn't been reliably reproduced yet",
    "a design decision on how to structure a new caching layer",
    "an edge case in a file upload flow with very large files",
    "a dependency version conflict that needs more investigation",
    "understanding a legacy piece of code before it can safely be refactored",
    "a UI inconsistency across browsers that needs cross-testing",
    "clarifying requirements for the next feature before implementation",
]

PLANS = [
    "continue implementing the remaining form fields and add validation",
    "write additional test coverage for today's changes",
    "start investigating the pending performance issue in more depth",
    "pair with a teammate to unblock an open design question",
    "review feedback on today's pull request and address comments",
    "begin work on the next module in the curriculum",
    "refactor today's code based on what was learned today",
    "revisit the unresolved challenge with a fresh approach",
    "document today's solution for future reference",
    "prepare for the next mentor session by listing open questions",
]


def join_natural(items):
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def build_content():
    tasks = random.sample(TASKS, k=random.randint(2, 3))
    tasks_text = "Today I spent time " + join_natural(tasks) + "."
    solved_text = "I " + random.choice(CHALLENGES_SOLVED) + "."
    pending_text = "I'm still working through " + random.choice(CHALLENGES_PENDING) + "."
    plan_text = "Tomorrow I plan to " + random.choice(PLANS) + "."
    return tasks_text, solved_text, pending_text, plan_text


def fill_question(page, title, text):
    page.locator('div[role="listitem"]', has_text=title).locator("textarea").fill(text)


def submit():
    tasks_text, solved_text, pending_text, plan_text = build_content()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="auth_state.json")
        page = context.new_page()
        page.goto(FORM_URL, wait_until="networkidle")

        try:
            checkbox = page.get_by_role("checkbox").first
            if checkbox.count() and not checkbox.is_checked():
                checkbox.check()
        except Exception:
            pass

        page.get_by_role("radio", name="It was a working day, and I was present").click()
        page.get_by_role("button", name="Next").click()
        page.wait_for_timeout(1500)
        page.wait_for_load_state("networkidle")

        fill_question(page, "What were your key tasks for the day?", tasks_text)
        fill_question(page, "did you solve today?", solved_text)
        fill_question(page, "NOT able to solve today", pending_text)
        fill_question(page, "plan for the next day of Simulated Work", plan_text)

        page.get_by_role("button", name="Next").click()
        page.wait_for_timeout(1500)
        page.wait_for_load_state("networkidle")

        page.get_by_role("button", name="Submit").click()
        page.wait_for_timeout(1500)
        page.wait_for_load_state("networkidle")

        content = page.content().lower()
        if "recorded" not in content and "thank you" not in content:
            page.screenshot(path="submit_failure.png", full_page=True)
            browser.close()
            sys.exit("Submission may have failed — confirmation text not found.")

        print("Form submitted successfully.")
        print("Tasks:", tasks_text)
        print("Solved:", solved_text)
        print("Pending:", pending_text)
        print("Plan:", plan_text)
        browser.close()


if __name__ == "__main__":
    submit()
