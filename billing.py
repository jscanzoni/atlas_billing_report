import requests
import csv
import json
import os
from collections import defaultdict
from requests.auth import HTTPDigestAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
public_key = os.getenv("PUBLIC_KEY")
private_key = os.getenv("PRIVATE_KEY")
org_id = os.getenv("ORG_ID")
atlas_base_url = "https://cloud.mongodb.com/api/atlas/v1.0"

# Create invoices directory if it doesn't exist
os.makedirs("invoices", exist_ok=True)

# Get list of invoices for the organization


def get_invoices(org_id):
    url = f"{atlas_base_url}/orgs/{org_id}/invoices?pageNum=1&itemsPerPage=100"
    response = requests.get(url, auth=HTTPDigestAuth(public_key, private_key))
    response.raise_for_status()
    # Get only the first three invoices
    return response.json().get("results", [])[:3]

# Get detailed information for a specific invoice


def get_invoice_details(org_id, invoice_id):
    url = f"{atlas_base_url}/orgs/{org_id}/invoices/{invoice_id}"
    response = requests.get(url, auth=HTTPDigestAuth(public_key, private_key))
    response.raise_for_status()
    return response.json()

# Allocate missing costs proportionally across projects


def allocate_missing_costs(project_costs, missing_cost):
    total_cost = sum(project_costs.values())
    allocation = {}
    for project, cost in project_costs.items():
        allocation[project] = (cost / total_cost) * \
            missing_cost if total_cost > 0 else 0
    return allocation

# Main function to process invoices and output CSV


def main():
    invoices = get_invoices(org_id)

    for invoice in invoices:
        invoice_id = invoice.get("id")
        start_date = invoice.get("startDate", "N/A")
        end_date = invoice.get("endDate", "N/A")

        invoice_details = get_invoice_details(org_id, invoice_id)
        # Retrieve creditsCents from the invoice details payload
        credits_cents = invoice_details.get("creditsCents", 0)
        line_items = invoice_details.get("lineItems", [])

        project_costs = defaultdict(int)
        missing_cost = 0

        # Sum up all totalPriceCents by groupName (project)
        for item in line_items:
            group_name = item.get("groupName")
            total_price_cents = item.get("totalPriceCents", 0)

            if group_name:
                project_costs[group_name] += total_price_cents
            else:
                missing_cost += total_price_cents

        # Allocate missing costs proportionally
        allocation = allocate_missing_costs(project_costs, missing_cost)

        # Prepare CSV output data
        all_allocations = []
        for project, cost in project_costs.items():
            allocated_cost = allocation.get(project, 0)
            project_total_cents = cost + allocated_cost

            all_allocations.append({
                "invoice_id": invoice_id,
                "start_date": start_date,
                "end_date": end_date,
                "project_name": project,
                # Up to 10 decimal places
                "allocation_percentage": round((cost / sum(project_costs.values())) * 100, 10) if sum(project_costs.values()) > 0 else 0,
                "line_item_total_cents": cost,  # Original line item cost in cents
                "project_total_cents": project_total_cents,  # Allocated total cost in cents
                # Convert cents to dollars for summary
                "project_total_dollars": project_total_cents / 100.0
            })

        # Adjust the allocation if there is a difference between calculated total and creditsCents
        calculated_total_cents = sum(
            # Work in cents
            item["project_total_cents"] for item in all_allocations)
        difference = credits_cents - calculated_total_cents

        if difference != 0 and all_allocations:

            print("----")
            print(f"Invoice ID: {invoice_id}")
            print(f"Start Date: {start_date}")
            print(f"Sum of project_total_cents: {calculated_total_cents}")
            print(f"creditsCents (from invoice details): {credits_cents}")
            print(f"Difference: {difference}")

            # Apply difference to the first project in cents
            all_allocations[0]["project_total_cents"] += difference
            # Update dollars accordingly
            all_allocations[0]["project_total_dollars"] = all_allocations[0]["project_total_cents"] / 100.0
            print(
                f"***ADJUSTED IN PROJECT: {all_allocations[0]['project_name']}***")

            print("----")

        # Write results to a separate CSV for each invoice
        if start_date != "N/A":
            yyyy_mm = start_date[:7]  # Extract yyyy-mm from start_date
        else:
            yyyy_mm = "unknown"
        csv_filename = f"invoices/{yyyy_mm}-{invoice_id}.csv"

        with open(csv_filename, "w", newline="") as csvfile:
            fieldnames = ["invoice_id", "start_date", "end_date", "project_name", "allocation_percentage",
                          "line_item_total_cents", "project_total_cents", "project_total_dollars"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for row in all_allocations:
                writer.writerow(row)

        print(f"CSV file '{csv_filename}' has been generated.")


if __name__ == "__main__":
    main()
