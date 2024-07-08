import requests # ...for parsing HTML content
from bs4 import BeautifulSoup # ...for scraping web content
import pymupdf # ...for reading PDFs
import os
import csv

# Function to extract href values from <a> elements with class "card__link"
def get_href_values(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', class_='card__link')
    return [link.get('href') for link in links]

# Generate URLs 
base_url = "https://www.judiciary.uk/pfd-types/suicide-from-2015/page/"

# ...Adjust below based on desired pages to scrape
start_page = 1
end_page = 58

urls = [f"{base_url}{i}" for i in range(start_page, end_page)]

# Iterate through all URLs and extract href values
all_href_values = []
for url in urls:
    href_values = get_href_values(url)
    all_href_values.extend(href_values)

# Print the result
for index, href_value in enumerate(all_href_values, start=1):
    print(f"Link {index}: {href_value}")

# Function to clean text
def clean_text(text):
    return ' '.join(text.split())

# Function to extract text from PDF
def extract_text_from_pdf(pdf_url):
    response = requests.get(pdf_url)
    with open("temp.pdf", "wb") as pdf_file:
        pdf_file.write(response.content)

    pdf_document = pymupdf.open("temp.pdf")
    text = ""
    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]
        text += page.get_text()
    pdf_document.close()
    os.remove("temp.pdf")
    return clean_text(text)

# Function to get report info and write to CSV
def get_report_info(url, writer):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}")
        return
    soup = BeautifulSoup(response.content, 'html.parser')
    pdf_links = [a['href'] for a in soup.find_all('a', class_='govuk-button')]
    if not pdf_links:
        print(f"No PDF links found on {url}")
        return

    report_link = pdf_links[0]
    pdf_text = extract_text_from_pdf(report_link)
    
    date_element = soup.find(lambda tag: tag.name == 'p' and 'Date of report:' in tag.get_text(), recursive=True)
    ref_element = soup.find(lambda tag: tag.name == 'p' and 'Ref:' in tag.get_text(), recursive=True)

    date = date_element.get_text() if date_element else 'N/A'
    report_id = ref_element.get_text() if ref_element else 'N/A'

    try:
        section1 = pdf_text.split(" SENT ")[1].split("CORONER")[0]
    except IndexError:
        section1 = "N/A"
    section1 = clean_text(section1)

    try:
        section2 = pdf_text.split(" CONCERNS ")[1].split(" 6 ACTION SHOULD BE TAKEN ")[0]
    except IndexError:
        section2 = "N/A"

    receiver = section1
    content = section2

    if receiver and content:
        receiver = '\n'.join(line for line in receiver.splitlines() if line.strip())
        content = '\n'.join(line for line in content.splitlines() if line.strip())
        
    writer.writerow([url, report_id, date, receiver, content])

# Create output CSV file in the `../Data` directory
parent_directory = os.path.join(os.pardir, "Data")
if not os.path.exists(parent_directory):
    os.makedirs(parent_directory)
output_file = os.path.join(parent_directory, "raw.csv")

with open(output_file, 'w', newline='', encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['URL', 'ID', 'Date', 'Receiver', 'Content'])
    for url in all_href_values:
        get_report_info(url, csv_writer)