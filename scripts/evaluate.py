import json
import sys

import requests

API_URL = "http://127.0.0.1:8000/query"

TEST_CASES = [
    {
        "description": "Test RAG Tool: Ask a question about report content.",
        "query": "What is the outlook for the EU cereals harvest?",
        "validator": lambda response: isinstance(response, str)
        and len(response) > 50
        and "not found" not in response.lower(),
    },
    {
        "description": "Test Data Tool: Ask for specific price figures.",
        "query": "Show me the latest price figures for feed wheat in Germany.",
        "validator": lambda r: isinstance(r, str)
        and all(kw in r.lower() for kw in ["price", "germany", "wheat", "€"]),
    },
    {
        "description": "Test Plotting Tool: Ask for a chart.",
        "query": "Plot a chart for feed maize in France.",
        "validator": lambda r: isinstance(r, str)
        and ".png" in r
        and "chart" in r.lower(),
    },
]


def run_evaluation():
    """
    Runs all defined test cases against the running API.
    """
    print("--- Starting Agent Evaluation ---")

    failures = 0

    for i, test in enumerate(TEST_CASES):
        print(f"\nRunning Test #{i + 1}: {test['description']}")
        print(f"Query: {test['query']}")

        try:
            response = requests.post(
                API_URL,
                data=json.dumps({"text": test["query"]}),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            agent_response = response.json().get("response")

            # Use the validator to check the response
            if test["validator"](agent_response):
                print("PASSED")
            else:
                print("FAILED: Response did not pass validation.")
                print(f"Agent Response: {agent_response}")
                failures += 1
        except requests.exceptions.RequestException as e:
            print(f"FAILED: Could not connect to the API. Error: {e}")
            failures += 1
            break
        except Exception as e:
            print(f"FAILED: An unexpected error occured. Error: {e}")
            failures += 1

    print("\n--- Evaluation Complete ---")
    if failures == 0:
        print("All tests passend successfully!")
    else:
        print(f"{failures} test(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    run_evaluation()
