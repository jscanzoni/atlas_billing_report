# MongoDB Atlas Invoice Allocation Script

This script connects to MongoDB Atlas APIs to retrieve organization-level invoices, process costs by project, and allocate any missing costs such as the support plan proportionally across projects. The output is a CSV file per invoice, summarizing the cost breakdown for each project.

## Requirements

- Python 3.7+
- MongoDB Atlas Org-level Billing Viewer API Key
- `python-dotenv` library to manage environment variables
- `requests` library to handle API calls

## Setup

1. **Clone the Repository**: Clone this repository to your local machine.

2. **Install Required Packages**: Install the required Python libraries. You can add them to a `requirements.txt` and run:
   ```sh
   pip install -r requirements.txt
   ```
   Example `requirements.txt`:
   ```
   requests
   python-dotenv
   ```

3. **Create a `.env` File**: In the root directory of your project, create a `.env` file with the following content:
   ```
   PUBLIC_KEY=your_public_key_here
   PRIVATE_KEY=your_private_key_here
   ORG_ID=your_org_id_here
   ```
   - Replace `your_public_key_here` and `your_private_key_here` with your MongoDB Atlas API keys.
   - Replace `your_org_id_here` with your MongoDB Atlas organization ID.

4. **API Key Permissions**: Ensure the API key has **Org-level Billing Viewer** permissions to retrieve billing details.

## Running the Script

To run the script, simply execute:
```sh
python billing.py
```

The script will:
- Fetch up to three invoices for the given organization.
- For each invoice, retrieve line items and calculate costs for each project.
- Allocate any missing costs proportionally across projects.
- Save the output for each invoice as a CSV file in the `invoices` directory.

## Sample Output

The CSV files will be saved in the `invoices` folder and named using the following pattern: `yyyy-mm-<invoice_id>.csv`, where `yyyy` and `mm` come from the invoice's start date.

The CSV files contain the following columns:
- `invoice_id`: The ID of the invoice.
- `start_date`: Start date of the invoice period.
- `end_date`: End date of the invoice period.
- `project_name`: Name of the project.
- `allocation_percentage`: Percentage of the project cost compared to the total project cost.
- `line_item_total_cents`: Original line item cost in cents.
- `project_total_cents`: Allocated total cost in cents.
- `project_total_dollars`: Total cost converted to dollars.

## Notes

- If there is a discrepancy between the sum of all `project_total_cents` and `creditsCents` from the invoice, the difference is adjusted in the first project. The adjustment is logged to the console. This should only be cents if at all.

- Ensure you have appropriate permissions on your MongoDB Atlas account to access the required billing details.

## Troubleshooting

- **Invalid API Key**: Ensure your `PUBLIC_KEY` and `PRIVATE_KEY` in the `.env` file are correct and have appropriate permissions.
- **Missing Environment Variables**: Ensure all the required environment variables are present in the `.env` file.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

