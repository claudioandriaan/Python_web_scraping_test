# Web Scraping Project

This project is designed to scrape listing and detail pages from a website and store the extracted data into Google Sheets. Additionally, it downloads images from the detail pages and uploads them to an FTP server.

## Setup

1. **Clone the Repository**: 
git clone https://github.com/claudioandriaan/web_scraping_python_test.git 

2. **Install Dependencies**:
```
  pip install BeautifulSoup
  
  pip install selenium 
  
  pip install gspread 
  
  pip install ftputil 
  
  pip install requests 

``` 

4. **Set Up Google API Credentials**:
- Obtain Google API credentials (JSON file) and save it as `dot.json` in the project directory.

4. **Configure FTP Credentials**:
- Update the FTP server details (host, username, password) in the `scrape_data_from_link()` function in the script.

5. **Run the Script**:
```
python spiders.py -d <output_directory>
```
