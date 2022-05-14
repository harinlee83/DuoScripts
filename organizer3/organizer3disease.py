# Component 2b: Build a script which can parse Column I and search for a list of diseases (from the DOID and MONDO), and when a term or terms are
# identified, add a corresponding permanent URL (PURL) for each in a new column, Column K (DOID) and Column L (MONDO). This may involve adding
# multiple PURLs to a column. It will limit PURLs to the top 5.

# This code builds off of code from organizer2.py
# This code works with Requests package and API calls to extract data from https://www.ebi.ac.uk/ols/index

import csv
from urllib.parse import quote
import pandas
import concurrent.futures
import re
from myFunctions import get_JSON, get_Purl, construct_URL

def main():

    # Insert "consent title" column letter (captialized) here
    consent_title_column_letter = input("Insert consent title column letter (capitalized): ")
    CONSENT_TITLE_COLUMN_NUMBER = ord(consent_title_column_letter) - ord("A")

    # Insert "DOID PURL" column letter (captialized) here
    doid_purl_column_letter = input("Insert DOID PURL column letter (capitalized): ")
    DOID_PURL_COLUMN_NUMBER = ord(doid_purl_column_letter) - ord("A")
    name_of_DOID_PURL_column = "DOID PURLs"

    # Insert "MONDO PURL" column letter (captialized) here
    mondo_purl_column_letter = input("Insert MONDO PURL column letter (capitalized): ")
    MONDO_PURL_COLUMN_NUMBER = ord(mondo_purl_column_letter) - ord("A")
    name_of_MONDO_PURL_column = "MONDO PURLs"

    original_CSV_file = "csv files/ORGANIZED_v2: DUO Validation Project - Development Dataset - Sheet1.csv"
    new_CSV_file = "csv files/ORGANIZED_v3: DUO Validation Project - Development Dataset - Sheet1.csv"

    # Read in consent title columns all at once (as opposed to line by line) using pandas (python data analysis library)
    # so that you store them all in an array

    fileArray = pandas.read_csv(original_CSV_file)
    consentTitleArray = fileArray['consent_title']

    doidPurls = []
    mondoPurls = []
    queryList = ["DISEASE", "SPECIFIC"]
    pattern = re.compile(r'^' + queryList[0] + r'[ -]' + queryList[1] + r'[ \(|\()]')

    # Populate empty lists with Purls
    for item in consentTitleArray:
        # Looks for "DISEASE SPECIFIC" or "DISEASE-SPECIFIC"
        matches = re.search(pattern,str(item).upper())
        # If found, this finds the first term in parenthesis in a non-greedy fashion
        if matches:
            parenthesisPattern = re.compile(r'\((.*?)[\,\)]')
            result = re.search(parenthesisPattern,item)
            item = result.group(1)
        else:
            # If no match, set as empty string
            item = ""
        # This ensures that the query term is URL encoded
        doidPurls.append(construct_URL(quote(item),0,True))
        mondoPurls.append(construct_URL(quote(item),0,False))

    # Using concurrent futures module to speed up "get requests" with threading
    with concurrent.futures.ThreadPoolExecutor() as executer:
        doidResults = list(executer.map(get_Purl, doidPurls))
        mondoResults = list(executer.map(get_Purl, mondoPurls))

    with open(original_CSV_file, "r") as originalFile:    
        with open(new_CSV_file, "w") as newFile:

            reader = csv.reader(originalFile)
            writer = csv.writer(newFile)

            # Store the column headers, add a new PURL column, print them in newFile
            columnHeaders = next(reader)
            columnHeaders.insert(DOID_PURL_COLUMN_NUMBER,name_of_DOID_PURL_column)
            columnHeaders.insert(MONDO_PURL_COLUMN_NUMBER,name_of_MONDO_PURL_column)
            writer.writerow(columnHeaders)

            for iterator, line in enumerate(reader):
                # Make a changeable copy of current line
                copyLine = line.copy()

                # Insert empty cell
                copyLine.insert(DOID_PURL_COLUMN_NUMBER,'')
                copyLine.insert(MONDO_PURL_COLUMN_NUMBER,'')

                # Insert DOID PURLs into file
                for purl in doidResults[iterator]:
                    copyLine[DOID_PURL_COLUMN_NUMBER] = copyLine[DOID_PURL_COLUMN_NUMBER] + purl + '\n'
                copyLine[DOID_PURL_COLUMN_NUMBER] = copyLine[DOID_PURL_COLUMN_NUMBER].strip()
                            
                # Insert MONDO PURLs into file
                for purl in mondoResults[iterator]:
                    copyLine[MONDO_PURL_COLUMN_NUMBER] = copyLine[MONDO_PURL_COLUMN_NUMBER] + purl + '\n'
                copyLine[MONDO_PURL_COLUMN_NUMBER] = copyLine[MONDO_PURL_COLUMN_NUMBER].strip()
                    
                writer.writerow(copyLine)
                iterator += 1

if __name__ == "__main__":
    main()
