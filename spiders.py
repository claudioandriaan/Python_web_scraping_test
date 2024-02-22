import os
import re 
import argparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import gspread
import ftputil
import requests

def store_data_in_google_sheet(data):
    try:        
        gc = gspread.service_account(filename='dot.json')
        sh = gc.open('Test_web_scraping').sheet1
        
        sh.append_row([data[0], data[1], data[2], data[3], data[4]])  # Fixed indexing
        
        print("Data stored in Google Sheets successfully.")
        return 
    except  Exception as e:
        print("Error storing data in Google Sheets:", e)

def extract_data_from_website(driver, site_url, page_number, listing_dir):
    try:
        driver.get(site_url)
        driver.implicitly_wait(10)
        page_source = driver.page_source
        listing_page_dir = os.path.join(listing_dir, "LISTING")
        if not os.path.exists(listing_page_dir):
            os.makedirs(listing_page_dir)
        with open(os.path.join(listing_page_dir, f"page-{page_number}.html"), "w", encoding="utf-8") as f:
            f.write(page_source)

        soup = BeautifulSoup(page_source, "html.parser")
        items = soup.find_all('div', class_="col-3 item__wrapper")

        return parse_data(items)

    except Exception as e:
        print("Error retrieving website:", e)
        return []

def parse_data(items):
    extracted_data = []
    for item in items:
        link = "https://www.3suisses.fr" + item.find('a').get('href')
        extracted_data.append(link)
    return extracted_data

def parse_detail_page(page_source, output_file):
    try:
        soup = BeautifulSoup(page_source, "html.parser")
        
        image_element = soup.find('div', class_="owl-item").find('li').find('a')
        image_url = "https://www.3suisses.fr" + image_element.get('href') if image_element else ""
        
        price_element = soup.find('span', class_="dyn_prod_price")
        price = price_element.text.strip() if price_element else "0"

        name_element = soup.find('title')
        product_name = name_element.text.strip() if name_element else ""
        name = product_name.replace("| 3 SUISSES", "") if product_name else ""

        delivered_time_element = soup.find('span', class_="dyn_time_fret")
        delivered = delivered_time_element.text.strip() if delivered_time_element else ""

        p_tag = soup.find('span', class_="small-stock product__stock--nb")
        dispo = re.search(r'\d+', p_tag.text).group() if p_tag else "0"

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{name}\t{price}\t{image_url}\t{delivered}\t{dispo}\n")
            
        return (name, price, image_url, delivered, dispo)

    except Exception as e:
        print("Error parsing detail page:", e)

def scrape_data_from_link(driver, link, all_dir, output_file):
    try:
        page_filename = f"{os.path.basename(link)}.html"
        page_file = os.path.join(all_dir, "ALL", page_filename)
        if os.path.exists(page_file):
            with open(page_file, "r", encoding="utf-8") as f:
                page_source = f.read()
        else:
            driver.get(link)
            driver.implicitly_wait(10)
            page_source = driver.page_source
            with open(page_file, "w", encoding="utf-8") as f:
                f.write(page_source)
        
        print(f"Data scraped for {link}")

        return parse_detail_page(page_source, output_file)  # Return extracted data

    except Exception as e:
        print(f"Error scraping data from {link}: {e}")
        return None  # Return None if an error occurs



def scrape_detail_pages(links, all_dir, output_file):
    try:
        extracted_data = []
        firefox_options = FirefoxOptions()
        firefox_options.headless = False
        firefox_options.log.level = "trace"
        with webdriver.Firefox(options=firefox_options) as driver:
            for link in links:
                link = link.strip()
                data = scrape_data_from_link(driver, link, all_dir, output_file)
                if data:
                    extracted_data.append(data)  # Append extracted data
        if extracted_data:
            for data_row in extracted_data:
                store_data_in_google_sheet(data_row)  # Store each data row in Google Sheets
                download_and_upload_image(data_row[2])  # Download and upload image to FTP

    except Exception as e:
        print("An error occurred:", e)

def download_and_upload_image(image_url):
    try:
        local_filename = os.path.basename(image_url)
        with open(local_filename, 'wb') as f:
            f.write(requests.get(image_url).content)

        # FTP Upload
        with ftputil.FTPHost('server', 'user_name', 'passwors') as host:
            host.chdir('images_trois_suisses')  # Change to your desired directory on FTP server
            host.upload(local_filename, local_filename)
            print(f"Image uploaded to FTP server: {image_url}")

        os.remove(local_filename)  # Remove the local file after uploading

    except Exception as e:
        print(f"Error downloading/uploading image: {e}")

def main():
    parser = argparse.ArgumentParser(description="Scrape listing and detail pages.")
    parser.add_argument("-d", "--output_directory", type=str, help="Output directory for storing pages")
    args = parser.parse_args()

    if not args.output_directory:
        print("Please provide an output directory using -d or --output_directory option.")
        return

    output_file = os.path.join(args.output_directory, "extract.tab")
    if os.path.exists(output_file):
        os.remove(output_file)  

    try:
        max_page = 11
        extracted_data = []
        firefox_options = FirefoxOptions()
        firefox_options.headless = False  
        firefox_options.log.level = "trace"  

        # Create ALL and LISTING directories if they don't exist
        all_dir = os.path.join(args.output_directory, "ALL")
        listing_dir = os.path.join(args.output_directory, "LISTING")
        for directory in [all_dir, listing_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

        with webdriver.Firefox(options=firefox_options) as driver:
            for page in range(1, max_page + 1):
                site_url = f'https://www.3suisses.fr/C-6176038-canapes--fauteuils.htm?page={page}'
                print('Scraped url : ' + site_url)
                extracted_data.extend(extract_data_from_website(driver, site_url, page, args.output_directory))

        scrape_detail_pages(extracted_data, args.output_directory, output_file)

    except Exception as e:
        print("An error occurred:", e)


if __name__ == "__main__":
    main()
