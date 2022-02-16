 # @Author: Min Li
 # @Email: mli.bio@outlook.com
 # @Last Modified by: Min Li
 # @Timestamp for Last Modification: 2022-02-13 18:38:39
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

from xml.sax.handler import ContentHandler
from xml.sax import parse
import pandas as pd
import re

class ExtractData(ContentHandler):

    def __init__(self):
        # Mapping dict
        self.dbid_dname = {}
        self.dbid_indicati = {}
        self.dbid_inchi = {}
        self.dbid_tgid = {}
        self.tgid_gname = {}
        # Current Drug ID, Target ID, and Indication
        self.curr_id = ""
        self.tgid = ""
        self.indicati = ""
        # Limitation of traversal area
        self.limit = 0

    # Called when traversing to the beginning of the label.
    def startElement(self, name, attrs):
        if name == "drug":
            self.limit = 1
            
        elif self.limit == 1 and name == "drugbank-id" and attrs:
            if attrs["primary"] == "true":
                self.limit = 2

        elif self.limit == 3 and name == "name":
            self.limit = 4

        elif name == "indication":
            self.limit = 5
            
        elif name == "calculated-properties":
            self.limit = 6
            
        elif self.limit == 6 and name == "kind":
            self.limit = 6.1
            
        elif self.limit == 6.2 and name == "value":
            self.limit = 6.3
            
        elif name == "target":
            self.limit = 7
            
        elif self.limit == 7 and name == "polypeptide":
            self.dbid_tgid.setdefault(self.curr_id, set()).add(attrs["id"])
            self.tgid = attrs["id"]
            self.limit = 8
            
        elif self.limit == 8 and name == "gene-name":
            self.limit = 9

    # Get the content of the traversed tag, such as <ele>content.....</ele>.
    def characters(self, content):
        if self.limit == 2:
            # Bug fix: DB02937
            if content == "DB":
                content = "DB02937"
            self.curr_id = content
            self.limit = 3

        elif self.limit == 4:
            self.dbid_dname[self.curr_id] = content
            self.limit = 0

        elif self.limit == 5:
            # Information on indications usually has multiple lines, paste them.
            self.indicati += content
            
        elif self.limit == 6.1:
            if content == "InChI":
                self.limit = 6.2
                
        elif self.limit == 6.3:
            # Bug fix: DB14488
            if content == "InCh":
                content = "InChI=1S/2C6H12O7.Fe/c2*7-1-2(8)3(9)4(10)5(11)6(12)13;/h2*2-5,7-11H,1H2,(H,12,13);/q;;+2/p-2/t2*2-,3-,4+,5-;/m11./s1"
            self.dbid_inchi[self.curr_id] = content
            self.limit = 0
            
        elif self.limit == 9:
            self.tgid_gname[self.tgid] = content
            self.limit = 0
            
    # Called when the traversal to the end of the label.
    def endElement(self, name):
        if name == "indication":
            # Remove blank lines between lines.
            self.indicati = re.sub("\r\n\r\n", "\r\n", self.indicati)
            self.dbid_indicati[self.curr_id] = self.indicati
            self.indicati = ""
            self.limit = 0
        if name == "drugbank":
            self.limit = 10

    # Called at the end of the traversal.
    def endDocument(self):
        if self.limit == 10:
            # Get mapping relationship between DrugBank ID and Drug Name.
            list1_key = []
            list1_val = []
            for key,val in self.dbid_dname.items():
                list1_key.append(key)
                list1_val.append(val)
            data_dict = {"DrugID":list1_key, "DrugName":list1_val}
            file1 = pd.DataFrame(data_dict)
            file1.to_csv("XML_dbid_dname.csv", index = False)

            # Get mapping relationship between DrugBank ID and Indication.
            list2_key = []
            list2_val = []
            for key,val in self.dbid_indicati.items():
                list2_key.append(key)
                list2_val.append(val)
            data_dict = {"DrugID":list2_key, "Indication":list2_val}
            file2 = pd.DataFrame(data_dict)
            file2.to_csv("XML_dbid_indicati.csv", index = False)

            # Get mapping relationship between DrugBank ID and Drug InChI.
            list3_key = []
            list3_val = []
            for key,val in self.dbid_inchi.items():
                list3_key.append(key)
                list3_val.append(val)
            data_dict = {"DrugID":list3_key, "InChI":list3_val}
            file3 = pd.DataFrame(data_dict)
            file3.to_csv("XML_dbid_inchi.csv", index = False)

            # Get mapping relationship between DrugBank ID and Target ID.
            list4_key = []
            list4_val = []
            for key,val in self.dbid_tgid.items():
                list4_key.append(key)
                list4_val.append(list(val))
            file4 = pd.DataFrame(index = list4_key, data = list4_val)
            file4.index.name = "DrugID"
            file4.to_csv("XML_dbid_tgid.csv")

            # Get mapping relationship between TargetID and DrugBank ID
            tgid_dbid = {}
            for key,val in self.dbid_tgid.items():
                for v in val:
                    tgid_dbid.setdefault(v, list()).append(key)
            file5 = pd.DataFrame(index = list(tgid_dbid.keys()), data = tgid_dbid.values())
            file5.index.name = "UniprotAC"
            file5.to_csv("XML_tgid_dbid.csv")

            # Get mapping relationship between Target ID and GeneName.
            list6_key = []
            list6_val = []
            for key,val in self.tgid_gname.items():
                list6_key.append(key)
                list6_val.append(val)
            data_dict = {"UniprotAC":list6_key, "GeneName":list6_val}
            file6 = pd.DataFrame(data_dict)
            file6.to_csv("XML_tgid_gname.csv", index = False)

            # print(file1)
            # print(file2)
            # print(file3)
            # print(file4)
            # print(file5)
            # print(file6)

            # print(self.dbid_dname)
            # print(self.dbid_indicati)
            # print(self.dbid_inchi)
            # print(self.dbid_tgid)
            # print(tgid_dbid)

parse('drugbank_5-1-9.xml', ExtractData())
