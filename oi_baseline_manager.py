from pathlib import Path
from datetime import datetime
import shutil
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

CLOSING_FILE = Path(
    "option_chain_base_oi_closing.csv"
)

OPENING_FILE = Path(
    "option_chain_base_oi_opening.csv"
)

def show_file_details(label, file_path):

    print(f"\n{label}")
    print("-" * 50)
    print(f"File   : {file_path}")

    if not file_path.exists():
        print("Status : NOT FOUND")
        return False

    modified = datetime.fromtimestamp(
        file_path.stat().st_mtime,
        tz=IST
    )

    print("Status : FOUND")
    print(
        "Date   :",
        modified.strftime("%d-%m-%Y")
    )
    print(
        "Time   :",
        modified.strftime("%I:%M:%S %p")
    )

    return True


def ask_yes_no(message):
    while True:
        answer = input(message).strip().lower()

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no"):
            return False

        print("Please enter Y or N.")


def morning_baseline_check():
    print("\n" + "=" * 55)
    print("OI BASELINE MAINTENANCE")
    print("=" * 55)

    closing_exists = show_file_details(
        "CLOSING OI FILE",
        CLOSING_FILE
    )

    opening_exists = show_file_details(
        "OPENING BASELINE FILE",
        OPENING_FILE
    )

    if not closing_exists:
        print(
            "\nClosing OI file is not available."
        )
        print(
            "It will normally be created by main.py "
            "after 15:30."
        )

    retain_opening = ask_yes_no(
        "\nRetain existing Opening Baseline? (Y/N): "
    )

    if retain_opening:
        if opening_exists:
            print(
                "Existing Opening Baseline retained."
            )
            return True

        print(
            "Opening Baseline does not exist."
        )

        if not closing_exists:
            print(
                "Cannot create Opening Baseline because "
                "Closing OI file is missing."
            )
            return False

        create_opening = ask_yes_no(
            "Create Opening Baseline from Closing OI? "
            "(Y/N): "
        )

        if not create_opening:
            print("No baseline file changed.")
            return False

    if not closing_exists:
        print(
            "Opening Baseline cannot be updated because "
            "Closing OI file is missing."
        )
        return False

    print("\nProposed update:")
    print(f"FROM : {CLOSING_FILE}")
    print(f"TO   : {OPENING_FILE}")

    confirm = ask_yes_no(
        "Confirm Closing OI → Opening Baseline? "
        "(Y/N): "
    )

    if not confirm:
        print(
            "Opening Baseline update cancelled."
        )
        return False

    try:
        shutil.copy2(
            CLOSING_FILE,
            OPENING_FILE
        )

        print(
            "\nOpening Baseline updated successfully."
        )

        show_file_details(
            "UPDATED OPENING BASELINE FILE",
            OPENING_FILE
        )

        return True

    except Exception as error:
        print(
            "Opening Baseline update failed:",
            error
        )
        return False