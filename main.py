from nt import write
import re
from lxml import etree
import os
import pandas as pd
import json
import requests
from datetime import datetime


def calculate_gst_invoice_total(taxable_value, rate):
    gst_amount = taxable_value * rate/100
    invoice_total = taxable_value + gst_amount
    invoice_info = {
        "Invoice Value": invoice_total,
        "GST": gst_amount,
    }
    return invoice_info

def validate_gstin(gstin):
    pattern = r"^([0][1-9]|[1-2][0-9]|[3][0-7])([a-zA-Z]{5}[0-9]{4}[a-zA-Z]{1}[1-9a-zA-Z]{1}[zZ]{1}[0-9a-zA-Z]{1})+$"
    if re.fullmatch(pattern, gstin):
        return True
    return False

def get_state_code(gstin):
    """Extracts first 2 digits (state code) from GSTIN"""
    return gstin[:2] if len(gstin) >= 2 else None

def create_sale_voucher(invoice_number, gstin, party_ledger_name, invoice_date, rate, taxable_value, narration="", company_name="Test", company_region="07", xml_file="templates/create_sales_vouchers.xml"):
    def generate_remote_id(bill_no: int) -> str:
        return f"{bill_no:08d}"

    def convert_to_tally_date_format(invoice_date):
        try:
            # Parse the input string into a datetime object
            invoice_date = str(invoice_date)
            dt = datetime.strptime(invoice_date, "%Y-%m-%d %H:%M:%S")
        # Format as compact YYYYMMDD
            return dt.strftime("%Y%m%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Expected 'YYYY-MM-DD HH:MM:SS'. Error: {str(e)}")

    if not os.path.exists(xml_file):
        raise FileNotFoundError(f"XML file not found: {xml_file}")
    
    with open (xml_file, 'r', encoding="utf-8") as file:
        xml_content = file.read()

    intrastate_xml_entry = "<ALLLEDGERENTRIES.LIST> \
						<LEDGERNAME>CGST@9%</LEDGERNAME> \
						<GSTCLASS/> \
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> \
						<LEDGERFROMITEM>No</LEDGERFROMITEM> \
						<REMOVEZEROENTRIES>No</REMOVEZEROENTRIES> \
						<ISPARTYLEDGER>No</ISPARTYLEDGER> \
						<AMOUNT>{{GST_AMOUNT}}</AMOUNT> \
					</ALLLEDGERENTRIES.LIST> \
                    <ALLLEDGERENTRIES.LIST> \
						<LEDGERNAME>SGST@9%</LEDGERNAME> \
						<GSTCLASS/> \
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> \
						<LEDGERFROMITEM>No</LEDGERFROMITEM> \
						<REMOVEZEROENTRIES>No</REMOVEZEROENTRIES> \
						<ISPARTYLEDGER>No</ISPARTYLEDGER> \
						<AMOUNT>{{GST_AMOUNT}}</AMOUNT> \
					</ALLLEDGERENTRIES.LIST> "

    interstate_xml_entry = "<ALLLEDGERENTRIES.LIST> \
						<LEDGERNAME>IGST@18%</LEDGERNAME> \
						<GSTCLASS/> \
						<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE> \
						<LEDGERFROMITEM>No</LEDGERFROMITEM> \
						<REMOVEZEROENTRIES>No</REMOVEZEROENTRIES> \
						<ISPARTYLEDGER>No</ISPARTYLEDGER> \
						<AMOUNT>{{GST_AMOUNT}}</AMOUNT> \
					</ALLLEDGERENTRIES.LIST>"

    invoice_info = calculate_gst_invoice_total(taxable_value, rate)

    invoice_value = invoice_info['Invoice Value']
    invoice_date = convert_to_tally_date_format(invoice_date)
    gst_amount = invoice_info['GST']
    narration = f"Being Bill No. {invoice_number}"

    remote_id_prefix = generate_remote_id(invoice_number)

    # XML escape special characters
    import html
    escaped_company_name = html.escape(company_name)
    escaped_party_ledger_name = html.escape(party_ledger_name)
    escaped_narration = html.escape(narration)
    
    xml_content = xml_content.replace("{{COMPANY_NAME}}", escaped_company_name) \
                            .replace("{{INVOICE_DATE}}", str(invoice_date)) \
                            .replace("{{PARTY_LEDGER_NAME}}", escaped_party_ledger_name) \
                            .replace("{{INVOICE_VALUE}}", str(invoice_value)) \
                            .replace("{{GUID_PREFIX}}", str(remote_id_prefix)) \
                            .replace("{{TAXABLE_VALUE}}", str(taxable_value)) \
                            .replace("{{NARRATION}}", escaped_narration)

    print(gstin)

    is_gstin = validate_gstin(gstin)
    print(is_gstin)
    if is_gstin:
        gst_state_code = get_state_code(gstin)
        print(gst_state_code)
        if gst_state_code == company_region:
            xml_content = xml_content.replace("{{SALES_LEDGER}}", "Sales@18%-IntraState")
            xml_content = xml_content.replace("{{GST_ENTRY}}", intrastate_xml_entry)
            xml_content = xml_content.replace("{{GST_AMOUNT}}", str(gst_amount/2))
        else:
            xml_content = xml_content.replace("{{SALES_LEDGER}}", "Sales@18%-InterState")
            xml_content = xml_content.replace("{{GST_ENTRY}}", interstate_xml_entry)
            xml_content = xml_content.replace("{{GST_AMOUNT}}", str(gst_amount))

    try:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.fromstring(xml_content.encode('utf-8'), parser)
        xml_data = etree.tostring(tree, pretty_print=True, encoding='unicode')
        print(xml_data)
        return post_xml_to_tally(xml_data)

    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XML format: {str(e)}")
    
            

    

def create_ledger(ledger_name, parent_ledger_name, company_name="Test", xml_file="templates/create_ledger.xml"):
    if not os.path.exists(xml_file):
        raise FileNotFoundError(f"XML file not found: {xml_file}")
    
    with open (xml_file, 'r', encoding="utf-8") as file:
        xml_content = file.read()

    # XML escape special characters
    import html
    escaped_ledger_name = html.escape(ledger_name)
    escaped_parent_ledger_name = html.escape(parent_ledger_name)
    escaped_company_name = html.escape(company_name)
    
    xml_content = xml_content.replace("{{LEDGER_NAME}}", escaped_ledger_name) \
                            .replace("{{PARENT_LEDGER_NAME}}", escaped_parent_ledger_name) \
                            .replace("{{COMPANY_NAME}}", escaped_company_name) \
                            .replace("{{CURRENCY_NAME}}", "Rs.") \
                            .replace("{{IS_BILL_WISE_ON}}", "No") \
                            .replace("{{IS_COST_CENTRE_ON}}", "No") \
                            .replace("{{IS_INTEREST_ON}}", "No") \
                            .replace("{{ALLOW_IN_MOBILE}}", "No") \
                            .replace("{{IS_CONDENSED}}", "No") \
                            .replace("{{AFFECTS_STOCK}}", "No") \
                            .replace("{{FOR_PAY_ROLL}}", "No") \
                            .replace("{{INTEREST_ON_BILL_WISE}}", "No") \
                            .replace("{{OVERRIDE_INTEREST}}", "No") \
                            .replace("{{OVERRIDE_ADV_INTEREST}}", "No") \
                            .replace("{{USE_FORVAT}}", "No") \
                            .replace("{{IGNORE_TDS_EXEMPT}}", "No") \
                            .replace("{{IS_TCS_APPLICABLE}}", "No") \
                            .replace("{{IS_TDS_APPLICABLE}}", "No") \
                            .replace("{{IS_FBT_APPLICABLE}}", "No") \
                            .replace("{{IS_GST_APPLICABLE}}", "No") \
                            .replace("{{IS_EXCISE_APPLICABLE}}", "No") \
                            .replace("{{SHOW_IN_PAY_SLIP}}", "No") \
                            .replace("{{USE_FOR_GRATUITY}}", "No") \
                            .replace("{{FOR_SERVICE_TAX}}", "No") \
                            .replace("{{IS_INPUT_CREDIT}}", "No") \
                            .replace("{{IS_EXMEPTED}}", "No") \
                            .replace("{{IS_ABATEMENT_APPLICABLE}}", "No") \
                            .replace("{{TDS_DEDUCTEE_IS_SPECIAL_RATE}}", "No") \
                            .replace("{{FONT}}", "No") \
                            .replace("{{IS_AUDITED}}", "No") \
                            .replace("{{SORT_POSITION}}", "1000") \
                            .replace("{{LANGUAGE_ID}}", "1033")

    try:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.fromstring(xml_content.encode('utf-8'), parser)
        xml_data = etree.tostring(tree, pretty_print=True, encoding='unicode')
        return post_xml_to_tally(xml_data)

    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XML format: {str(e)}")

def check_ledger_exists(ledger_name, company_name="Test", xml_file="templates/get_ledger.xml"):
    if not os.path.exists(xml_file):
        raise FileNotFoundError(f"XML file not found: {xml_file}")
    
    with open(xml_file, 'r', encoding='utf-8') as file:
        xml_content = file.read()
    
    # XML escape special characters
    import html
    escaped_ledger_name = html.escape(ledger_name)
    escaped_company_name = html.escape(company_name)
    
    xml_content = xml_content.replace("{{LEDGER_NAME}}", escaped_ledger_name) \
                           .replace("{{COMPANY_NAME}}", escaped_company_name)
    
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.fromstring(xml_content.encode('utf-8'), parser)
        xml_data = etree.tostring(tree, pretty_print=True, encoding='unicode')
        xml_response = post_xml_to_tally(xml_data)
        parsed_xml_response = etree.fromstring(xml_response.encode('utf-8'))
        if xml_response:
            names = parsed_xml_response.xpath('//NAME/text()')
            name = names[0] if names else False
            if name == ledger_name:
                return True
            else:
                return False
        else:
            print("no ledger found")
            
    except etree.XMLSyntaxError as e:
        raise ValueError(f"Invalid XML after replacement: {str(e)}")

    

def post_xml_to_tally(xml_data):
    url = "http://localhost:9000"
    headers = {
        "Content-Type": "application/xml",  
        "Accept": "application/xml"         
    }

    # 3. Send POST request
    try:
        response = requests.post(
            url,
            data=xml_data.encode('utf-8'),  
            headers=headers,
            timeout=10 
        )
        
        # Check response
        if response.status_code == 200:
            print("Success! Tally Response:")
            return response.text
        else:
            print(f"Error {response.status_code}: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Connection failed: {str(e)}")

with open('mappers/GSTR1_excel_mapper.json', 'r', encoding='utf-8') as file:
    column_mapper = json.load(file)

df = pd.read_excel('GSTR1_JULY_2024.xlsx', sheet_name="b2b,sez,de", header=[3])

reverse_mapper = {v: k for k, v in column_mapper.items()}
df = df.rename(columns=reverse_mapper)

mapped_columns = list(column_mapper.keys())
data = df[mapped_columns].dropna(how='all')

list_of_dicts = data.to_dict('records')

for invoice in list_of_dicts:
    party_name = invoice.get('party_name')
    print(f"Processing ledger: {party_name}")
    
    checkLedger = check_ledger_exists(
        ledger_name=party_name,
        company_name="Test"
    )

    print(checkLedger)

    if checkLedger:
        createSaleVoucher = create_sale_voucher(
            invoice_number=invoice.get('invoice_no'),
            gstin=invoice.get('gstin'),
            party_ledger_name=invoice.get('party_name'),
            invoice_date=invoice.get('invoice_date'),
            taxable_value=invoice.get('taxable_amount'),
            rate=invoice.get('gst_rate')
        )

        print(createSaleVoucher)

        
    else:
        createLedger = create_ledger(
            parent_ledger_name="Sundry Creditors",
            ledger_name=invoice.get('party_name')
        )

        print(createLedger)
