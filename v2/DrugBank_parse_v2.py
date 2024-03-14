 # @Author: Min Li
 # @Email: mli.bio@outlook.com
 # @Last Modified by: Min Li2024-03-14 11:14:59
 # @Timestamp for Last Modification: 
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

# 解析状态枚举，定义不同的解析阶段
class ParseState(Enum):
    INIT = auto()  # 初始化
    IN_DRUG = auto()  # 在 drug 元素内
    IN_DRUGBANK_ID = auto()  # 正在解析 drugbank-id 元素
    IN_DRUGNAME = auto()  # 正在解析 druganame
    IN_NAME = auto()  # 正在解析 name 元素
    IN_INDICATION = auto()  # 正在解析 indication 元素
    IN_CALCULATED_PROPERTIES = auto()  # 在 calculated-properties 元素内
    IN_KIND = auto()  # 正在解析 kind 元素
    IN_KIND_INCHI = auto()  # 正在解析 kind 为 InChI 的元素
    IN_VALUE = auto()  # 正在解析 value 元素
    IN_TARGET = auto()  # 在 target 元素内
    IN_POLYPEPTIDE = auto()  # 在 polypeptide 元素内
    IN_GENE_NAME = auto()  # 正在解析 gene-name 元素
    RESET = auto()  # 重置状态

class DrugDataExtractor(ContentHandler):
    """用于从 DrugBank 的 XML 文件中提取药物数据的类。"""

    def __init__(self):
        """初始化解析器和存储解析数据的字典。"""
        self.resetCurrentContext()
        self.dbidDname = {}  # 药物 ID 到药物名的映射
        self.dbidIndicati = {}  # 药物 ID 到适应症的映射
        self.dbidInchI = {}  # 药物 ID 到 InChI 的映射
        self.dbidTgid = {}  # 药物 ID 到靶标 ID 的映射
        self.tgidGname = {}  # 靶标 ID 到基因名的映射

    def resetCurrentContext(self):
        """重置当前解析上下文。"""
        self.currentIndication = ""
        self.currentState = ParseState.INIT

    def startElement(self, name, attrs):
        """元素开始标签的处理，根据元素名更改状态。"""
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
        """处理元素内的文本内容，根据当前状态处理文本内容。"""
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
        """元素结束标签的处理。"""
        if name == "indication":
            self.dbidIndicati[self.currentId] = re.sub("\r\n\r\n", "\r\n", self.currentIndication)
            self.resetCurrentContext()

    def endDocument(self):
        """文档解析结束时的处理，导出数据到文件。"""
        self.exportData()

    def addTgidForCurrentDrug(self, tgid):
        """为当前药物添加靶标 ID。"""
        self.dbidTgid.setdefault(self.currentId, set()).add(tgid)
        self.currentTgid = tgid
        self.currentState = ParseState.IN_POLYPEPTIDE

    def handleDrugId(self, content):
        """处理药物 ID，包括特定 ID 的修正。"""
        if content == "DB":
            content = "DB02937"
        self.currentId = content
        self.currentState = ParseState.IN_DRUGNAME

    def fixInChI(self, content):
        """特定 InChI 的修正。"""
        if content == "InCh":
            return "InChI=1S/2C6H12O7.Fe/c2*7-1-2(8)3(9)4(10)5(11)6(12)13;/h2*2-5,7-11H,1H2,(H,12,13);/q;;+2/p-2/t2*2-,3-,4+,5-;/m11./s1"
        return content

    def exportData(self):
        """导出解析得到的数据到 CSV 文件。"""
        # 导出药物 ID 到药物名的映射
        # print(f'dbidDname: {self.dbidDname}')
        pd.DataFrame.from_dict(self.dbidDname, orient='index', columns=['DrugName'])\
            .reset_index()\
            .rename(columns={'index': 'DrugID'})\
            .to_csv('XML_dbid_dname.csv', index=False)
        
        # 导出药物 ID 到适应症的映射
        # print(f'dbidIndicati: {self.dbidIndicati}')
        pd.DataFrame.from_dict(self.dbidIndicati, orient='index', columns=['Indication'])\
            .reset_index()\
            .rename(columns={'index': 'DrugID'})\
            .to_csv('XML_dbid_indicati.csv', index=False)
        
        # 导出药物 ID 到 InChI 的映射
        # print(f'dbidInchI: {self.dbidInchI}')
        pd.DataFrame.from_dict(self.dbidInchI, orient='index', columns=['InChI'])\
            .reset_index()\
            .rename(columns={'index': 'DrugID'})\
            .to_csv('XML_dbid_inchi.csv', index=False)
        
        # 导出药物 ID 到靶标 ID 的映射
        # 因为一个药物可能对应多个靶标 ID，所以这里稍微复杂一些
        tgidList = [(k, v) for k, vs in self.dbidTgid.items() for v in vs]
        # print(f'dbidTgid: {self.dbidTgid}')
        pd.DataFrame(tgidList, columns=['DrugID', 'TargetID'])\
            .to_csv('XML_dbid_tgid.csv', index=False)

        # 导出靶标 ID 到药物 ID 的映射
        # 一个靶标可能对应多个药物，因此需要反转 dbidTgid 字典
        tgidDbid = {}
        for drugId, targetIds in self.dbidTgid.items():
            for targetId in targetIds:
                if targetId in tgidDbid:
                    tgidDbid[targetId].append(drugId)
                else:
                    tgidDbid[targetId] = [drugId]
        # 将靶标 ID 到药物 ID 的映射转换为列表形式以便导出
        tgidDgidList = [(k, v) for k, vs in tgidDbid.items() for v in vs]
        # print(f'tgidDgidList: {tgidDgidList}')
        pd.DataFrame(tgidDgidList, columns=['UniprotAC', 'DrugID'])\
            .to_csv('XML_tgid_dbid.csv', index=False)

        # 导出靶标 ID 到基因名的映射
        # print(f'tgidGname: {self.tgidGname}')
        pd.DataFrame.from_dict(self.tgidGname, orient='index', columns=['GeneName'])\
            .reset_index()\
            .rename(columns={'index': 'UniprotAC'})\
            .to_csv('XML_tgid_gname.csv', index=False)

def parseDrugBankXml(filePath):
    """解析 DrugBank 的 XML 文件。"""
    parser = DrugDataExtractor()
    parse(filePath, parser)

parseDrugBankXml('drugbank_5-1-9.xml')
