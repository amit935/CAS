# Tally GST Data Entry Automation

This script automates the process of importing GST1 format Excel data into Tally ERP 9 using XML templates and the Tally ODBC server.

## Features

- Reads GST1 format Excel files using Pandas
- Automatically checks if ledgers exist in Tally
- Creates new ledgers if they don't exist
- Posts sales vouchers with GST details
- Comprehensive logging and error handling
- Configurable column mapping

## Prerequisites

1. **Tally ERP 9** installed and running
2. **Tally ODBC Server** enabled (port 9000)
3. **Python 3.7+** installed
4. Required Python packages (see requirements.txt)

## Installation

1. Clone or download this repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### 1. Update config.json
Edit `config.json` with your Tally company details:
```json
{
    "COMPANY_NAME": "Your Company Name",
    "CURRENCY": "INR"
}
```

### 2. Excel File Format
Your Excel file should have the following columns (or update the mapper):
- Invoice No.
- Invoice Date
- GSTIN
- Party Name
- Taxable Amount
- CGST Amount
- SGST Amount
- IGST Amount
- Total Amount

### 3. Column Mapping
If your Excel columns have different names, update `mappers/sale_excel_mapper.json`:
```json
{
    "excel_columns": {
        "invoice_no": "Your Invoice Column Name",
        "invoice_date": "Your Date Column Name",
        "gstin": "Your GSTIN Column Name",
        "party_name": "Your Party Name Column",
        "taxable_amount": "Your Taxable Amount Column",
        "cgst_amount": "Your CGST Column",
        "sgst_amount": "Your SGST Column",
        "igst_amount": "Your IGST Column",
        "total_amount": "Your Total Amount Column"
    }
}
```

## Usage

1. **Start Tally ERP 9** and ensure it's running
2. **Enable Tally ODBC Server** (port 9000)
3. **Open your company** in Tally
4. **Run the script**:
   ```bash
   python main.py
   ```
5. **Enter the path** to your GST1 Excel file when prompted

## How It Works

1. **Excel Reading**: The script reads your GST1 format Excel file using Pandas
2. **Data Validation**: Validates required columns and cleans the data
3. **Ledger Check**: For each party, checks if a ledger exists in Tally
4. **Ledger Creation**: If ledger doesn't exist, creates it using the XML template
5. **Voucher Posting**: Creates and posts sales vouchers with GST details
6. **Logging**: All operations are logged to `tally_automation.log`

## File Structure

```
tally-data-entry-automation/
├── main.py                          # Main automation script
├── config.json                      # Configuration file
├── requirements.txt                 # Python dependencies
├── README.md                       # This file
├── mappers/
│   └── sale_excel_mapper.json     # Column mapping configuration
└── templates/
    ├── create_ledger.xml          # Ledger creation template
    ├── create_sales_vouchers.xml  # Sales voucher template
    └── create_purchase_vouchers.xml # Purchase voucher template
```

## Troubleshooting

### Common Issues

1. **Connection Error**: Ensure Tally is running and ODBC server is enabled
2. **Company Not Found**: Check the company name in config.json
3. **Column Not Found**: Update the mapper file to match your Excel column names
4. **Permission Error**: Ensure you have write permissions for log files

### Logs

Check `tally_automation.log` for detailed error messages and operation logs.

## Customization

### Adding New Voucher Types

1. Create new XML templates in the `templates/` folder
2. Update the mapper files for different Excel formats
3. Modify the main script to handle different voucher types

### Modifying Ledger Groups

Edit `templates/create_ledger.xml` to change the parent group for new ledgers.

## Security Notes

- The script communicates with Tally on localhost:9000
- No sensitive data is transmitted externally
- All operations are logged for audit purposes

## Support

For issues or questions:
1. Check the log file for detailed error messages
2. Verify your Excel file format matches the expected columns
3. Ensure Tally is properly configured and running 