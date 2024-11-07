# DrugBank_parse

> Get information on drugs, targets and indications in DrugBank from downloaded XML file.
> Inspired by https://github.com/Deshan-Zhou/deal_DrugBank.

## Folder Description

- `v1`: An early version with fast parsing speed but obscure code.
- `v2`: Improved legibility, but slower file processing.
- `vR`: R version, much slower than the python version (about 25 times) and takes up very little memory (about 20M) during runtime.
- `dev`: Development version, using the `lxml` library to rewrite the parsing logic. ***Not finished yet***.

## File Description

- `DrugBank_parse.py`: This script implements a class to parse the xml file downloaded from DrugBank to obtain DrugID, DrugName, DrugInChI, TargetID, GeneName, Indications and their mapping relationship.
- `DrugBank_TDI.R`: This script is used to obtain the final target_drug_indication form of DrugBank.
- `test-database.xml`: A small test xml file containing the first drug of the xml file provided by the drugbank database.

You can get the xml file on https://go.drugbank.com/releases/latest. The current code has tested on release v5.1.12.

Detailed introductions can be found in the comments at the beginning of these scripts.

## dev log

The dev script currantly extract the following info:

- **All Drugs**: `list[dict]`
  - **DrugBankID**: `list[string]` - The primary DrugBank identifier for the drug.
  - **DrugName**: `list[string]` - The name of the drug.
  - **Description**: `list[string]` - A description of the drug.
  - **DrugReferences**: `list[dict]`
    - **PMID**: `string` - PubMed ID of the reference.
    - **Citation**: `string` - Citation text.
  - **Indication**: `list[string]` - The indication or medical use of the drug.
  - **DrugInteractions**: `list[dict]`
    - **InteractionDrugBankID**: `string` - DrugBank ID of the interacting drug.
    - **InteractionDrugName**: `string` - Name of the interacting drug.
    - **InteractionDescription**: `string` - Description of the drug interaction.
  - **CalculatedProperties**: `list[dict]`
    - **CalculatedPropertyKind**: `string` - The kind of calculated property (e.g., logP, molecular weight).
    - **CalculatedPropertyValue**: `string` - The value of the calculated property.
    - **CalculatedPropertySource**: `string` - The source of the calculated property.
  - **DrugExIdentifiers**: `list[dict]`
    - **Resource**: `string` - The resource name of the external identifier (e.g., UniProt, GenBank).
    - **Identifier**: `string` - The external identifier value.
  - **SNP**: `list[dict]`
    - **ProteinName**: `string` - Name of the protein affected by the SNP.
    - **GeneSymbol**: `string` - Gene symbol associated with the SNP.
    - **UniProtID**: `string` - UniProt ID associated with the SNP.
    - **RsID**: `string` - Reference SNP ID.
    - **DefiningChange**: `string` - The defining change of the SNP.
    - **Description**: `string` - Description of the SNP effect.
    - **PMID**: `string` - PubMed ID associated with the SNP effect.
  - **Targets**: `list[dict]`
    - **ID**: `string` - The DrugBank ID of the target.
    - **Name**: `string` - Name of the target.
    - **Organism**: `string` - Organism in which the target is found.
    - **Actions**: `list[string]` - List of actions of the drug on the target (e.g., inhibitor, agonist).
    - **References**: `list[dict]`
      - **PMID**: `string` - PubMed ID of the reference.
      - **Citation**: `string` - Citation text.
    - **Function**: `string` - General function of the target protein.
    - **FunctionDetails**: `string` - Specific function of the target protein.
    - **Chr**: `string` - Chromosome location.
    - **Locus**: `string` - Locus of the gene.
    - **Identifiers**: `list[dict]`
      - **Resource**: `string` - The resource name of the external identifier.
      - **Identifier**: `string` - The external identifier value.
    - **AminoAcidSequence**: `string` - Amino acid sequence of the target protein.
    - **GeneSequence**: `string` - Gene sequence associated with the target.
    - **Pfams**: `list[dict]`
      - **Identifier**: `string` - Pfam identifier.
      - **Name**: `string` - Pfam name.
    - **GO**: `list[dict]`
      - **Category**: `string` - GO category (component, function, process).
      - **Description**: `string` - GO description.
