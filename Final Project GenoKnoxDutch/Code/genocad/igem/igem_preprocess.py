from bs4 import BeautifulSoup

with open("xml_parts.xml", "rb") as f:
    content = f.read()

# Let BeautifulSoup fix broken XML
soup = BeautifulSoup(content, "xml")
print(soup.prettify()[:500])  # Print the first 500 characters to check the structure

parts = soup.find_all("part")

print(f"Parsed {len(parts)} parts")