# @Author: Min Li
# @Email: mli.bio@outlook.com
# @Last Modified by: Min Li
# @Timestamp for Last Modification: 2024-11-07 12:45:45
# @Description: This script implements a class to parse the xml file downloaded from DrugBank 
# to obtain DrugID, DrugName, DrugInChI, TargetID, GeneName, Indications and their mapping relationship.
# You can get the xml file on https://go.drugbank.com/releases/latest. This script has tested on release v5.1.12.

library(XML)
library(data.table)

rm(list = ls())

setwd("D:/Study/Project/DrugBank_parse/vR/")

# Define parsing state
states <- list(
  INIT = 1,
  IN_DRUG = 2,
  IN_DRUGBANK_ID = 3,
  IN_DRUGNAME = 4,
  IN_NAME = 5,
  IN_INDICATION = 6,
  IN_CALCULATED_PROPERTIES = 7,
  IN_KIND = 8,
  IN_KIND_INCHI = 9,
  IN_VALUE = 10,
  IN_TARGET = 11,
  IN_POLYPEPTIDE = 12,
  IN_GENE_NAME = 13,
  RESET = 14
)
currentState <- states$INIT

# Data structure definition
dbidDname <- data.table(DrugID = character(), DrugName = character())
dbidIndicati <- data.table(DrugID = character(), Indication = character())
dbidInchI <- data.table(DrugID = character(), InChI = character())
dbidTgid <- data.table(DrugID = character(), TargetID = character())
tgidGname <- data.table(UniprotAC = character(), GeneName = character())

currentId <- ""
currentIndication <- ""
currentTgid <- ""

# Processing of elements begins
startElement <- function(name, attrs) {
  globalVariables(c("currentState", "currentId", "currentTgid", "currentIndication"))
  
  if (name == "drug") {
    currentState <<- states$IN_DRUG
  } else if (currentState == states$IN_DRUG && name == "drugbank-id" && "primary" %in% names(attrs) && attrs["primary"] == "true") {
    currentState <<- states$IN_DRUGBANK_ID
  } else if (currentState == states$IN_DRUGNAME && name == "name") {
    currentState <<- states$IN_NAME
  } else if (name == "indication") {
    currentState <<- states$IN_INDICATION
  } else if (name == "calculated-properties") {
    currentState <<- states$IN_CALCULATED_PROPERTIES
  } else if (currentState == states$IN_CALCULATED_PROPERTIES && name == "kind") {
    currentState <<- states$IN_KIND
  } else if (currentState == states$IN_KIND_INCHI && name == "value") {
    currentState <<- states$IN_VALUE
  } else if (name == "target") {
    currentState <<- states$IN_TARGET
  } else if (currentState == states$IN_TARGET && name == "polypeptide") {
    currentTgid <<- attrs["id"]
    dbidTgid <<- rbind(dbidTgid, data.table(DrugID = currentId, TargetID = currentTgid))
    print(paste("Drug ID", currentId, "has Target ID:", currentTgid))  # Print the relationship between DrugID and TargetID
    currentState <<- states$IN_POLYPEPTIDE
  } else if (currentState == states$IN_POLYPEPTIDE && name == "gene-name") {
    currentState <<- states$IN_GENE_NAME
  }
}


# Process of element content
characters <- function(text) {
  globalVariables(c("currentId", "currentTgid", "currentState", "dbidDname", "dbidInchI", "dbidIndicati", "tgidGname"))
  
  if (currentState == states$IN_DRUGBANK_ID) {
    currentId <<- text
    print(paste("Current DrugBank ID:", currentId))  # Print drug ID
    currentState <<- states$IN_DRUGNAME
  } else if (currentState == states$IN_NAME) {
    dbidDname <<- rbind(dbidDname, data.table(DrugID = currentId, DrugName = text))
    print(paste("Drug Name for ID", currentId, ":", text))  # Print drug name
    currentState <<- states$RESET
  } else if (currentState == states$IN_INDICATION) {
    currentIndication <<- paste0(currentIndication, text)
    # print(paste("Accumulating Indication for ID", currentId, ":", currentIndication))  # Print cumulative indication content
  } else if (currentState == states$IN_KIND && text == "InChI") {
    currentState <<- states$IN_KIND_INCHI
  } else if (currentState == states$IN_VALUE) {
    dbidInchI <<- rbind(dbidInchI, data.table(DrugID = currentId, InChI = text))
    print(paste("InChI Value for ID", currentId, ":", text))  # Print InChI value
    currentState <<- states$RESET
  } else if (currentState == states$IN_GENE_NAME) {
    tgidGname <<- rbind(tgidGname, data.table(UniprotAC = currentTgid, GeneName = text))
    print(paste("Gene Name for Target ID", currentTgid, ":", text))  # Print gene name
    currentState <<- states$RESET
  }
}


# Processing of elements ends
endElement <- function(name) {
  globalVariables(c("currentId", "currentIndication", "currentState", "dbidIndicati"))
  
  if (name == "indication") {
    dbidIndicati <<- rbind(dbidIndicati, data.table(DrugID = currentId, Indication = currentIndication))
    print(paste("Storing Indication for ID", currentId, ":", currentIndication))  # Print stored indication content
    currentIndication <<- ""  # reset currentIndication
    currentState <<- states$RESET
  }
}


# Parse XML file
xmlEventParse("../test-database.xml", handlers = list(
  startElement = startElement,
  endElement = endElement,
  text = characters
), asText = FALSE, trim = TRUE)

# Remove duplicates
dbidDname <- unique(dbidDname)
dbidIndicati <- unique(dbidIndicati)
dbidInchI <- unique(dbidInchI)
dbidTgid <- unique(dbidTgid)
tgidGname <- unique(tgidGname)

# Export to CSV
fwrite(dbidDname, "R_dbid_dname.csv")
fwrite(dbidIndicati, "R_dbid_indicati.csv")
fwrite(dbidInchI, "R_dbid_inchi.csv")
fwrite(dbidTgid, "R_dbid_tgid.csv")
fwrite(tgidGname, "R_tgid_gname.csv")

