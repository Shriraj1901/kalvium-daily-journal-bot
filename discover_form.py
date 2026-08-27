"""
One-time interactive script.

Opens a real Chromium window and lets you log into your Google account manually.

Then it:
1. Saves the browser session to auth_state.json.
2. Attempts to extract the Google Form structure and saves it to:
   - form_structure_raw.json
   - form_structure.json

Run:
    python discover_form.py
"""

import json
import os
import re

from playwright.sync_api import sync_playwright


FORM_URL = os.getenv(
    "FORM_URL",
    "https://docs.google.com/forms/d/e/1FAIpQLSc8RRUAG8n8nPB9dm21m_MxwHQ-JuDnEj7GnvwEkWXykkKFuQ/viewform",
)


def safe_get(obj, indexes, default=None):
    """
    Safely access nested lists/dictionaries.

    Example:
        safe_get(data, [1, 8, 0, 3])
    """
    try:
        value = obj

        for index in indexes:
            if value is None:
                return default

            value = value[index]

        return value

    except (IndexError, KeyError, TypeError):
        return default


with sync_playwright() as p:

    # Launch a visible browser.
    browser = p.chromium.launch(headless=False)

    context = browser.new_context()

    page = context.new_page()

    print("Opening Google Form...")

    page.goto(
        FORM_URL,
        wait_until="domcontentloaded",
        timeout=60000,
    )

    input(
        "\nA browser window has opened.\n\n"
        "1. Log into your own Google account.\n"
        "2. Make sure you are on the actual Google Form.\n"
        "3. Make sure the form questions are visible.\n\n"
        "Once you can see the form, come back here and press Enter...\n"
    )

    # Give the page a moment to finish loading.
    try:
        page.wait_for_load_state(
            "networkidle",
            timeout=15000,
        )
    except Exception:
        print(
            "Network did not become completely idle. "
            "Continuing with the current page..."
        )

    # Get the page HTML.
    html = None

    for attempt in range(5):

        try:
            html = page.content()

            if html:
                break

        except Exception as error:

            print(
                f"Attempt {attempt + 1}/5 failed: {error}"
            )

            page.wait_for_timeout(1000)

    if html is None:

        browser.close()

        raise SystemExit(
            "Could not read the page HTML.\n"
            "Please re-run the script and wait longer "
            "before pressing Enter."
        )

    # Save the logged-in browser state.
    context.storage_state(
        path="auth_state.json"
    )

    print(
        "\nSaved logged-in session to auth_state.json"
    )

    # Try to find Google's embedded form data.
    match = re.search(
        r"var\s+FB_PUBLIC_LOAD_DATA_\s*=\s*(.*?);\s*</script>",
        html,
        re.S,
    )

    if not match:

        print(
            "\nCould not find FB_PUBLIC_LOAD_DATA_ "
            "in the page."
        )

        print(
            "Saving the page HTML for inspection..."
        )

        with open(
            "form_page.html",
            "w",
            encoding="utf-8",
        ) as file:

            file.write(html)

        print(
            "Saved raw HTML to form_page.html"
        )

    else:

        print(
            "\nFound FB_PUBLIC_LOAD_DATA_."
        )

        try:

            data = json.loads(
                match.group(1)
            )

        except json.JSONDecodeError as error:

            print(
                "\nCould not parse form data as JSON."
            )

            print(
                f"Error: {error}"
            )

            with open(
                "form_data_raw.txt",
                "w",
                encoding="utf-8",
            ) as file:

                file.write(
                    match.group(1)
                )

            print(
                "Saved raw data to form_data_raw.txt"
            )

            browser.close()

            raise SystemExit()

        # Save the complete raw structure.
        with open(
            "form_structure_raw.json",
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

        print(
            "Saved raw form structure "
            "to form_structure_raw.json"
        )

        # Try to extract the form title.
        title = safe_get(
            data,
            [1, 8, 0, 3],
            default=None,
        )

        if title:

            print(
                f"\nForm title: {title}"
            )

        else:

            print(
                "\nCould not safely extract "
                "the form title."
            )

        # Try to get the list of questions.
        items = safe_get(
            data,
            [1, 1],
            default=[],
        )

        if not isinstance(items, list):

            print(
                "\nCould not find the expected "
                "question list."
            )

            items = []

        questions = []

        for index, item in enumerate(
            items,
            start=1,
        ):

            try:

                # Extract question title.
                q_title = safe_get(
                    item,
                    [1],
                    default=None,
                )

                # Extract question type.
                q_type = safe_get(
                    item,
                    [3],
                    default=None,
                )

                # Extract entry block.
                entry_block = safe_get(
                    item,
                    [4, 0],
                    default=None,
                )

                if not entry_block:

                    print(
                        f"Skipping item {index}: "
                        "no entry block found."
                    )

                    continue

                # Entry ID.
                entry_id = safe_get(
                    entry_block,
                    [0],
                    default=None,
                )

                if entry_id is None:

                    print(
                        f"Skipping item {index}: "
                        "no entry ID found."
                    )

                    continue

                # Extract options.
                raw_options = safe_get(
                    entry_block,
                    [1],
                    default=None,
                )

                options = None

                if isinstance(
                    raw_options,
                    list,
                ):

                    options = []

                    for option in raw_options:

                        option_text = safe_get(
                            option,
                            [0],
                            default=None,
                        )

                        if option_text is not None:

                            options.append(
                                option_text
                            )

                # Required field.
                required = safe_get(
                    entry_block,
                    [2],
                    default=None,
                )

                question = {

                    "title": q_title,

                    "type_code": q_type,

                    "entry_id": (
                        f"entry.{entry_id}"
                    ),

                    "options": options,

                    "required": (
                        bool(required)
                        if required is not None
                        else None
                    ),

                }

                questions.append(
                    question
                )

            except Exception as error:

                print(
                    f"Skipping item {index} "
                    f"because of an extraction error: "
                    f"{error}"
                )

        # Save the simplified structure.
        output = {

            "form_title": title,

            "questions": questions,

        }

        with open(
            "form_structure.json",
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                output,
                file,
                indent=2,
                ensure_ascii=False,
            )

        print(
            f"\nExtracted {len(questions)} "
            "questions."
        )

        print(
            "Saved simplified structure "
            "to form_structure.json"
        )

        print("\nQuestions found:\n")

        for question in questions:

            print(
                f"- [{question['entry_id']}] "
                f"({question['type_code']}) "
                f"{question['title']!r}"
            )

            if question["options"]:

                print(
                    f"  Options: "
                    f"{question['options']}"
                )

            print(
                f"  Required: "
                f"{question['required']}"
            )

    print(
        "\nDone."
    )

    browser.close()