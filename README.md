# DrugBank_parse

> Get information on drugs, targets and indications in DrugBank from downloaded XML file.
> Inspired by https://github.com/Deshan-Zhou/deal_DrugBank.

## File Description

- DrugBank_parse.py: This script implements a class to parse the xml file downloaded from DrugBank to obtain DrugID, DrugName, DrugInChI, TargetID, GeneName, Indications and their mapping relationship. You can get the xml file on https://go.drugbank.com/releases/latest. Based upon release v5.1.9.
- DrugBank_TDI.R: This script is used to obtain the final target_drug_indication form of DrugBank.
- test-database.xml: A small test xml file containing the first drug of the xml file provided by the drugbank database.

Detailed introductions can be found in the comments at the beginning of these scripts.