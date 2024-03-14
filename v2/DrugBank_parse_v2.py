 # @Author: Min Li
 # @Email: mli.bio@outlook.com
 # @Last Modified by: Min Li
 # @Timestamp for Last Modification: 2024-03-14 16:46:00
 # @Description: This script implements a class to parse the xml file downloaded from DrugBank 
 # to obtain DrugID, DrugName, DrugInChI, TargetID, GeneName, Indications and their mapping relationship.
 # You can get the xml file on https://go.drugbank.com/releases/latest. This script is based upon v5.1.9.

 # Known bugs: 
 # All drugs are parsed normally, except DB02937 and DB14488.
 # DB02937 failed to retrieve DrugID and the extracted text is displayed as "DB";
 # DB14488 failed to retrieve DrugInChI and the extracted text is displayed as "InCh".
 # Useful imformation about the two drugs:
 # DrugName of DB02937: Gamma-Arsono-Beta, Gamma-Methyleneadenosine-5'-Diphosphate
 # DrugInChI of DB14488: InChI=1S/2C6H12O7.Fe/c2*7-1-2(8)3(9)4(10)5(11)6(12)13;/h2*2-5,7-11H,1H2,(H,12,13);/q;;+2/p-2/t2*2-,3-,4+,5-;/m11./s1

 # The cause of these bugs is unknown, perhaps there's a problem with the internal format of the file.
 # Fixed in line 87~89 and line 106~108.

 # Variable declaration:
 #     dbid     : DrugBank ID
 #     dname    : Drug Name
 #     indicati : Indication
 #     inchi    : Drug InChI
 #     tgid     : Target ID
 #     gname    : GeneName (Symbol)

from enum import Enum, auto
from xml.sax.handler import ContentHandler
from xml.sax import parse
import pandas as pd
import re

# Parsing status enumeration, defining different parsing stages
class ParseState(Enum):
    INIT = auto()  # Initialization
    IN_DRUG = auto()  # inside the drug element
    IN_DRUGBANK_ID = auto()  # Parsing drugbank-id element
    IN_DRUGNAME = auto()  # Parsing druganame
    IN_NAME = auto()  # Parsing name element
    IN_INDICATION = auto()  # Parsing indication element
    IN_CALCULATED_PROPERTIES = auto()  # inside the calculated-properties element
    IN_KIND = auto()  # Parsing kind element
    IN_KIND_INCHI = auto()  # Parsing the element whose kind is InChI
    IN_VALUE = auto()  # Parsing value element
    IN_TARGET = auto()  # inside the target element
    IN_POLYPEPTIDE = auto()  # inside the polypeptide element
    IN_GENE_NAME = auto()  # Parsing gene-name element
    RESET = auto()  # reset state

class DrugDataExtractor(ContentHandler):
    """Class for extracting drug data from DrugBank's XML files."""

    def __init__(self):
        """Initializes the parser and the dictionary that stores parsed data."""
        self.resetCurrentContext()
        self.dbidDname = {}  # Mapping from drug ID to drug name
        self.dbidIndicati = {}  # Mapping from drug ID to indication
        self.dbidInchI = {}  # Mapping from drug ID to InChI
        self.dbidTgid = {}  # Mapping from drug ID to target ID
        self.tgidGname = {}  # Mapping from target ID to gene name

    def resetCurrentContext(self):
        """Resets the current parsing context."""
        self.currentIndication = ""
        self.currentState = ParseState.INIT

    def startElement(self, name, attrs):
        """Processing of element start tags, changing status based on element name."""
        if name == "drug":
            self.currentState = ParseState.IN_DRUG
        elif self.currentState == ParseState.IN_DRUG and name == "drugbank-id" and "primary" in attrs:
            if attrs["primary"] == "true":
                self.currentState = ParseState.IN_DRUGBANK_ID
        elif self.currentState == ParseState.IN_DRUGNAME and name == "name":
            self.currentState = ParseState.IN_NAME
        elif name == "indication":
            self.currentState = ParseState.IN_INDICATION
        elif name == "calculated-properties":
            self.currentState = ParseState.IN_CALCULATED_PROPERTIES
        elif self.currentState == ParseState.IN_CALCULATED_PROPERTIES and name == "kind":
            self.currentState = ParseState.IN_KIND
        elif self.currentState == ParseState.IN_KIND_INCHI and name == "value":
            self.currentState = ParseState.IN_VALUE
        elif name == "target":
            self.currentState = ParseState.IN_TARGET
        elif self.currentState == ParseState.IN_TARGET and name == "polypeptide":
            self.addTgidForCurrentDrug(attrs["id"])
        elif self.currentState == ParseState.IN_POLYPEPTIDE and name == "gene-name":
            self.currentState = ParseState.IN_GENE_NAME

    def characters(self, content):
        """Process the text content within the element and process the text content according to the current state."""
        if self.currentState == ParseState.IN_DRUGBANK_ID:
            self.handleDrugId(content)
        elif self.currentState == ParseState.IN_NAME:
            self.dbidDname[self.currentId] = content
            self.currentState = ParseState.RESET
        elif self.currentState == ParseState.IN_INDICATION:
            self.currentIndication += content
        elif self.currentState == ParseState.IN_KIND and content == "InChI":
            self.currentState = ParseState.IN_KIND_INCHI
        elif self.currentState == ParseState.IN_VALUE:
            self.dbidInchI[self.currentId] = self.fixInChI(content)
            self.currentState = ParseState.RESET
        elif self.currentState == ParseState.IN_GENE_NAME:
            self.tgidGname[self.currentTgid] = content
            self.currentState = ParseState.RESET

    def endElement(self, name):
        """Handling of element closing tags."""
        if name == "indication":
            self.dbidIndicati[self.currentId] = re.sub("\r\n\r\n", "\r\n", self.currentIndication)
            self.resetCurrentContext()

    def endDocument(self):
        """Processing at the end of document parsing, exporting data to a file."""
        self.exportData()

    def addTgidForCurrentDrug(self, tgid):
        """Add target D to current drugs."""
        self.dbidTgid.setdefault(self.currentId, set()).add(tgid)
        self.currentTgid = tgid
        self.currentState = ParseState.IN_POLYPEPTIDE

    def handleDrugId(self, content):
        """Handles drug IDs, including corrections to specific IDs."""
        if content == "DB":
            content = "DB02937"
        self.currentId = content
        self.currentState = ParseState.IN_DRUGNAME

    def fixInChI(self, content):
        """Corrections of specific InChI."""
        if content == "InCh":
            return "InChI=1S/2C6H12O7.Fe/c2*7-1-2(8)3(9)4(10)5(11)6(12)13;/h2*2-5,7-11H,1H2,(H,12,13);/q;;+2/p-2/t2*2-,3-,4+,5-;/m11./s1"
        return content

    def exportData(self):
        """Export the parsed data to a CSV file."""
        # Export mapping from drug ID to drug name
        # print(f'dbidDname: {self.dbidDname}')
        pd.DataFrame.from_dict(self.dbidDname, orient='index', columns=['DrugName'])\
            .reset_index()\
            .rename(columns={'index': 'DrugID'})\
            .to_csv('XML_dbid_dname.csv', index=False)
        
        # Export mapping from drug ID to indication
        # print(f'dbidIndicati: {self.dbidIndicati}')
        pd.DataFrame.from_dict(self.dbidIndicati, orient='index', columns=['Indication'])\
            .reset_index()\
            .rename(columns={'index': 'DrugID'})\
            .to_csv('XML_dbid_indicati.csv', index=False)
        
        # Export mapping from drug ID to InChI
        # print(f'dbidInchI: {self.dbidInchI}')
        pd.DataFrame.from_dict(self.dbidInchI, orient='index', columns=['InChI'])\
            .reset_index()\
            .rename(columns={'index': 'DrugID'})\
            .to_csv('XML_dbid_inchi.csv', index=False)
        
        # Export mapping from drug ID to target ID
        # Since a drug may correspond to multiple target IDs, this is a little more complicated.
        tgidList = [(k, v) for k, vs in self.dbidTgid.items() for v in vs]
        # print(f'dbidTgid: {self.dbidTgid}')
        pd.DataFrame(tgidList, columns=['DrugID', 'TargetID'])\
            .to_csv('XML_dbid_tgid.csv', index=False)

        # Export mapping from target ID to drug ID
        # A target may correspond to multiple drugs, so the dbidTgid dictionary needs to be reversed.
        tgidDbid = {}
        for drugId, targetIds in self.dbidTgid.items():
            for targetId in targetIds:
                if targetId in tgidDbid:
                    tgidDbid[targetId].append(drugId)
                else:
                    tgidDbid[targetId] = [drugId]
        # Convert mapping from target ID to drug ID to list form for export
        tgidDgidList = [(k, v) for k, vs in tgidDbid.items() for v in vs]
        # print(f'tgidDgidList: {tgidDgidList}')
        pd.DataFrame(tgidDgidList, columns=['UniprotAC', 'DrugID'])\
            .to_csv('XML_tgid_dbid.csv', index=False)

        # Export mapping from target ID to gene name
        # print(f'tgidGname: {self.tgidGname}')
        pd.DataFrame.from_dict(self.tgidGname, orient='index', columns=['GeneName'])\
            .reset_index()\
            .rename(columns={'index': 'UniprotAC'})\
            .to_csv('XML_tgid_gname.csv', index=False)

def parseDrugBankXml(filePath):
    """Parse the DrugBank XML file."""
    parser = DrugDataExtractor()
    parse(filePath, parser)

parseDrugBankXml('drugbank_5-1-9.xml')
