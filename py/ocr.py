import os
import re
import time
import shutil
import easyocr
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from pdf2image import convert_from_path

tic = time.perf_counter()

baseDir = "C:/Users/TASH-PC/Desktop/bioOCR"
dependencies = baseDir + "/dependencies"
quickmart_pdfs = baseDir + "/quickmart pdfs"
non_quickmart_pdfs = baseDir + "/non quickmart pdfs"
error_files = baseDir + "/quickmart error files"
pdfs = baseDir + "/pdf"
txts = baseDir + "/txt"
pngs = baseDir + "/png"
xlsxs = baseDir + "/xlsx"

poppler_path = "C:/Users/TASH-PC/Desktop/bioOCR/dependencies/Release-21.11.0-0/poppler-21.11.0/Library/bin"

def ocr(image_path, filename, index):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path)
    with open(f"{txts}/{filename}-{index}.txt", "w", encoding="utf-8", errors="ignore") as f:
        for i in result:
            f.write(i[1])
            f.write('\n')
        print('Success')

def convert_pdf_to_images(pdf_path, filename):
    images = convert_from_path(pdf_path, poppler_path = poppler_path, dpi=500)
    for index, image in enumerate(images):
        image.save( pngs + f"/{filename}-{index}.PNG")
        print(f"{filename}.pdf successfully converted to png")
        ocr(( pngs + f"/{filename}-{index}.PNG"), filename, index)



## DEFINE FUNCTIONS

def convert(seconds):
    min, sec = divmod(seconds, 60)
    hour, min = divmod(min, 60)
    return "%d:%02d:%02d" % (hour, min, sec)


def fetchTableLineIDs (txtFile):
    lineCount = 0
    barcodes = []
    priceLineIDs = []
    brokenPiecesIDs = []
    actualDescriptionIDs = []
    possibleDescriptionIDs = []
    
    for line in txtFile.split("\n"):
        line = line.replace(",", "")

        if len(line) != 0:
            lineCount += 1
            
            line = re.sub(r"[()]", "", line)
            
            if re.match(r"^[1-9]{1,2}/", line):
                date = line.split(" ")[0]
                strippedDate = re.sub(r"[^A-Za-z0-9]+", "/", date)
                # !!SYSTEM UPDATE year = current year
                adjustedStrippedDate = strippedDate.split("/")[0] + "/" + strippedDate.split("/")[1] + "/2021" 
                # print(adjustedStrippedDate)
                formattedDate = datetime.strptime(adjustedStrippedDate, "%d/%m/%Y").date()
                # adding additional day for contract date
                nextDay = datetime.strftime((formattedDate + timedelta(days=1)), "%m/%d/%Y")
            
            elif re.match(r"^[\d]{1,2}-", line):
                date = line.split(" ")[0]
                months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
                day, currentMonth, year = date.split("-")[0], date.split("-")[1].lower(), date.split("-")[2]
                for i in range(len(months)):
                    if len(year) == 2:
                        year = "20" + year
                    if str(currentMonth) == months[i]:
                        newDate = day + "/" + str(i + 1) + "/" + year
                formattedDate = datetime.strptime(newDate, "%d/%m/%Y").date()
                # adding additional date for contract date
                nextDay = datetime.strftime((formattedDate + timedelta(days=1)), "%m/%d/%Y")
                
                
            elif re.search(r"# [0-9]{7}", line):
                purchaseOrderNumber = line.split(" ")[-1]
                
            elif re.match(r"^(\d{1,9}\.\d*|\.[1-9]{2})$", line):
                # print(line)
                priceLineIDs.append(lineCount)
                # line = line.replace(" ", "")
                # if re.match(r"^(\d{2,9}\.\d*|\.[1-9]{2})$", line):
                #     priceLineIDs.append(lineCount)
            
            elif re.match(r"[0-9]{11,15}", line):
                barcodes.append(line)
                
            elif re.match(r"PCS", line) != None:
                brokenPiecesIDs.append(lineCount - 1)
                line.replace("PCS", "")

            elif re.match(r"00 PCS", line) != None:
                brokenPiecesIDs.append(lineCount - 1)
                line.replace("00 PCS", "")
                
            elif re.match(r"^FD-|BIO-|BIO |FD |BIO", line) and len(line) > 3:
                if re.match(r"^BIO FOOD", line):
                    continue
                else:
                    actualDescriptionIDs.append(lineCount)
                possibleDescriptionIDs.append(lineCount + 1)
                
            elif re.search(r"for Branch|Branch$", line) != None:
                branchID = lineCount + 1
                        
    branchName = fetchBrand (txtFile, branchID)
            
    singleItemsPrices, totalItemPrices = verifyPriceIDs(txtFile, priceLineIDs)
    
    itemQuantities, itemDescriptions = checkBrokenLines (txtFile, brokenPiecesIDs, actualDescriptionIDs, possibleDescriptionIDs)
        
    return branchName, barcodes, singleItemsPrices, totalItemPrices, nextDay, purchaseOrderNumber, itemQuantities, itemDescriptions

def fetchBrand (txtFile, branchID):
    lineCount = 0
    for line in txtFile.split("\n"):
         if len(line) != 0:
            lineCount += 1
            if lineCount == branchID:
                branch = line
            
    return branch
    
def verifyPriceIDs (txtFile, priceIDs):
    lineCount = 0
    singleItemPrices = []
    totalItemPrices = []
    
    for id in priceIDs:
        currentID = id
        nextID = id + 1
        prevID = id - 1
        if nextID not in priceIDs and prevID not in priceIDs:
            priceIDs.remove(currentID)
            
    for line in txtFile.split("\n"):
         if len(line) != 0:
            lineCount += 1
            if lineCount in priceIDs:
                if priceIDs.index(lineCount) == 0 or priceIDs.index(lineCount) % 2 == 0:
                    singleItemPrices.append(line)
                else:
                    totalItemPrices.append(line)
    
    return singleItemPrices, totalItemPrices

def checkBrokenLines (txtFile, brokenIDs, actualDescriptionIDs, possibleDescriptionIDs):
    quantities = []
    fulDescriptions = []
    actualDescriptions = []
    possibleDescriptions = []
    
    lineCount = 0
    for line in txtFile.split("\n"):
        
        if len(line) != 0:
            lineCount += 1
            if lineCount in brokenIDs:
                if re.match(r"^[1-9]", line):
                    if len(line.strip()) != 0:
                        line = line + " PCS"
                        if re.match(r"1 PCS", line):
                            continue
                        else:
                            quantities.append(line)
            elif re.search(r"00 PCS|0u PCS|0U PCS$", line) != None:
                quantities.append(line)

    quantities = [re.sub("[^1-9]", "", q) for q in quantities]
    new_quantities = []
    for i in quantities:
        if len(i) > 0:
            new_quantities.append(int(i))  

    #############
    lineCount2 = 0
    for line in txtFile.split("\n"):
         if len(line) != 0:
            lineCount2 += 1
            if (lineCount2) in actualDescriptionIDs:
                actualDescriptions.append(line)
            elif lineCount2 in possibleDescriptionIDs:
                possibleDescriptions.append(line) 
            
    for i in range((len(possibleDescriptions))):
        if re.search(r"pcs$", possibleDescriptions[i].lower()) != None:
            fullDesc = actualDescriptions[i]
            fulDescriptions.append(fullDesc)
            
        else:
            fullDesc = actualDescriptions[i] + possibleDescriptions[i]
            fulDescriptions.append(fullDesc)
            
    return new_quantities, fulDescriptions


###############################################################
# RUN PROGRAM

print("BOOTING UP OCR BOT.... ")

time.sleep(5)

filenames = [f.split(".")[0] for f in os.listdir(pdfs) if f.endswith(".pdf") or f.endswith(".PDF")]
count = len(filenames)
print(f"{count} FILES DETECTED. PREPARING TO CONVERT.....")

time.sleep(3)

for name in filenames:
    print(f"Converting {name}.pdf")
    convert_pdf_to_images((pdfs + "/" + name + ".pdf"), name)
    count = count - 1
    print("SUCCESS")
    print(f"######  {count} files remaining.  ######")
    print("\n")

txtfilenames = [f.split(".")[0] for f in os.listdir(txts) if f.endswith(".txt")]
count = len(txtfilenames)
print(f"{count} FILES DETECTED. PREPARING TO PARSE TEXT.....")

time.sleep(3)

for name in txtfilenames:
    print(f"Parsing {name}.txt")
    with open((txts + "/" + name + ".txt"), encoding="utf-8", errors="ignore") as f:
        txtFile = f.read()

    loop_counter = 0
    
    for line in txtFile.split("\n"):
        line = line.replace(",", "")
        loop_counter += 1

        while len(line) != 0 and loop_counter < 2:
            loop_counter += 1
            line = line.strip(".")
            if re.match(r"^P|QUICK", line):
                print("QUICKMART PDF")
                allowOCR = True
            else:
                print("NOT QUICKMART PDF")
                allowOCR = False

    
    if allowOCR == True:
        customerBranch, productBarcodes, singleItemInvoicePrices, totalItemInvoicePrices, contractDate, contractNumber, orderItemQuantities, orderItemDescriptions = fetchTableLineIDs(txtFile)

        if (len(productBarcodes) == len(orderItemQuantities) == len(orderItemDescriptions)) and (len(productBarcodes) > 0):

            customerNames = pd.read_csv((dependencies + "/customer names.csv"))
            for index, row in customerNames.iterrows():
                if customerBranch in row["LPO NAME"]:
                    book_365_name = row[1]
                    break

            conversionFile = pd.read_csv((dependencies + "/conversion files.csv"))

            conversionFile["BARCODES"] = conversionFile["BARCODES"].astype("string")
            conversionFile = conversionFile.rename(columns={"AC" : "SKU", "PD" : "BOOK 365 DESC"})

            outputTable = pd.DataFrame({"LPO CUSTOMER NAME": (customerBranch), "BOOK 365 NAME": book_365_name, "WAREHOUSE": "FGStore", "CONTRACT NUMBER": contractNumber, "CONTRACT DATE": contractDate, "DOCUMENT DATE":contractDate, "DESC OCR": orderItemDescriptions, "BARCODES": productBarcodes, "QUANTITY": orderItemQuantities})
            outputTable["BARCODES"] = outputTable["BARCODES"].astype("string")

            orderedColumnNames = ["LPO CUSTOMER NAME", "BOOK 365 NAME", "DOCUMENT DATE", "WAREHOUSE", "CONTRACT NUMBER", "CONTRACT DATE", "SKU", "QUANTITY", "BARCODES", "DESC OCR", "BOOK 365 DESC", "Pieces"]

            mergedOutputConversion = pd.merge(outputTable, conversionFile, how="left", left_on="BARCODES", right_on="BARCODES")

            finalTable = mergedOutputConversion[orderedColumnNames]
            
            trays = []
            for index, row in finalTable.iterrows():
                trays.append(finalTable.iloc[index, 7]/finalTable.iloc[index, 11])

            finalTable.loc[:, "TRAYS"] = trays

            print(f"Saving {name}.xlsx")

            time.sleep(3)

            finalTable.to_excel((xlsxs + "/" + name + ".xlsx"), index=False)

            count = count - 1
            print("SUCCESS")
            print(f"{count} files remaining.")

            toc = time.perf_counter()
            duration = convert(tic-toc)

            print("The program runtime is {}".format(duration))
            print("\n")

            if f"{name[:-2]}.pdf" in os.listdir(pdfs):
                shutil.move((pdfs + f"/{name[:-2]}.pdf"), (quickmart_pdfs))

            elif f"{name[:-2]}.PDF" in os.listdir(pdfs):
                shutil.move((pdfs + f"/{name[:-2]}.PDF"), (quickmart_pdfs))

        elif (len(productBarcodes) != len(orderItemQuantities)) or (len(productBarcodes) != len(orderItemDescriptions)) or (len(orderItemQuantities) != len(orderItemDescriptions)):
            print(f"Encountered system error. Check {name}.pdf")
            shutil.move((pdfs + f"/{name[:-2]}.pdf"), (error_files))
            count = count - 1

            print("SUCCESS")
            print(f"{count} files remaining.")
            print("\n")
            continue

        elif (len(productBarcodes) == len(orderItemQuantities) == len(orderItemDescriptions) == 0):
            count = count - 1

            print("SUCCESS")
            print(f"{count} files remaining.")
            print("\n")
            continue

    else:
        if f"{name[:-2]}.pdf" in os.listdir(pdfs):
            shutil.move((pdfs + f"/{name[:-2]}.pdf"), (non_quickmart_pdfs))

        elif f"{name[:-2]}.PDF" in os.listdir(pdfs):
            shutil.move((pdfs + f"/{name[:-2]}.PDF"), (non_quickmart_pdfs))

        count = count - 1
        print("SUCCESS")
        print(f"{count}files remaining.")
        print("\n")
        continue

print("CLEANING SYSTEM CACHE. Please Wait...")
print("\n")
for img in os.listdir(pngs):
    os.remove(pngs + f"/{img}")

time.sleep(10)

print("############### FILE CONVERSION COMPLETE. ###############")


    
# fetchTableLineIDs(txtFile)

# for i in range (len(productBarcodes)):
#     print(productBarcodes[i], orderItemDescriptions[i])
 
# print(len(productBarcodes), len(orderItemQuantities), len(orderItemDescriptions))
################################################################