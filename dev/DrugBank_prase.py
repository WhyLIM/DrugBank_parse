# 船新版本
from lxml import etree

# 解析 XML 文件
tree = etree.parse('test-database.xml')

# 由于 XML 使用了命名空间，我们需要正确处理这些命名空间来找到我们感兴趣的元素
# 定义命名空间字典
nameSpaces = {'db': 'http://www.drugbank.ca'}

# 提取所有的 <drug>
drugs = tree.xpath('/db:drugbank/db:drug', namespaces=nameSpaces)

allDrugs = []

for drug in drugs:
    drugbankId = drug.xpath('db:drugbank-id[@primary="true"]/text()', namespaces=nameSpaces)
    # 药物名称
    drugName = drug.xpath('db:name/text()', namespaces=nameSpaces)
    # 药物描述
    description = drug.xpath('db:description/text()', namespaces=nameSpaces)
    # 参考文献信息
    drugReferences = drug.xpath("db:general-references/db:articles/db:article", namespaces=nameSpaces)
    drugRefs = []
    for dgRef in drugReferences:
        pubmedID = dgRef.find('db:pubmed-id', namespaces=nameSpaces).text if dgRef.find('db:pubmed-id', namespaces=nameSpaces) is not None else None
        citation = dgRef.find('db:citation', namespaces=nameSpaces).text if dgRef.find('db:citation', namespaces=nameSpaces) is not None else None
        drugRefs.append({
            'PMID': pubmedID, 
            'citation': citation
        })
    # 适应症
    indication = drug.xpath('db:indication/text()', namespaces=nameSpaces)

    # 药物相互作用
    drugInteractions = drug.xpath('db:drug-interactions/db:drug-interaction', namespaces=nameSpaces)
    drugInter = []
    for dgInt in drugInteractions:
        interdbID = dgInt.find('db:drugbank-id', namespaces=nameSpaces).text if dgInt.find('db:drugbank-id', namespaces=nameSpaces) is not None else None
        name = dgInt.find('db:name', namespaces=nameSpaces).text if dgInt.find('db:name', namespaces=nameSpaces) is not None else None
        description = dgInt.find('db:description', namespaces=nameSpaces).text if dgInt.find('db:description', namespaces=nameSpaces) is not None else None
        drugInter.append({
            'Interaction_DrugBankID': interdbID,
            'Interaction_drugName': name,
            'Interaction_description': description
        })

    # 计算属性
    calcProperties = drug.xpath('db:calculated-properties/db:property', namespaces=nameSpaces)
    calcProp = []
    for cp in calcProperties:
        kind = cp.find('db:kind', namespaces=nameSpaces).text if cp.find('db:kind', namespaces=nameSpaces) is not None else None
        value = cp.find('db:value', namespaces=nameSpaces).text if cp.find('db:value', namespaces=nameSpaces) is not None else None
        source = cp.find('db:source', namespaces=nameSpaces).text if cp.find('db:source', namespaces=nameSpaces) is not None else None
        calcProp.append({
            'Calculated_Property_Kind': kind,
            'Calculated_Property_Value': value,
            'Calculated_Property_Source': source
        })

    # 其他数据库中的标识符
    drugExIdentifiers = drug.xpath("db:external-identifiers/db:external-identifier", namespaces=nameSpaces)
    drugIdentifiers = []
    for exIdentifier in drugExIdentifiers:
        resource = exIdentifier.find('db:resource', namespaces=nameSpaces).text if exIdentifier.find('db:resource', namespaces=nameSpaces) is not None else None
        identifier = exIdentifier.find('db:identifier', namespaces=nameSpaces).text if exIdentifier.find('db:identifier', namespaces=nameSpaces) is not None else None
        drugIdentifiers.append({
            'resource': resource,
            'identifier': identifier
        })

    # SNP 作用
    snpEffects = drug.xpath("db:snp-effects/db:effect", namespaces=nameSpaces)
    snps = []
    for snpEffect in snpEffects:
        proteinName = snpEffect.find('db:protein-name', namespaces=nameSpaces).text if snpEffect.find('db:protein-name', namespaces=nameSpaces) is not None else None
        geneSymbol = snpEffect.find('db:gene-symbol', namespaces=nameSpaces).text if snpEffect.find('db:gene-symbol', namespaces=nameSpaces) is not None else None
        UniProtID = snpEffect.find('db:uniprot-id', namespaces=nameSpaces).text if snpEffect.find('db:uniprot-id', namespaces=nameSpaces) is not None else None
        rsID = snpEffect.find('db:rs-id', namespaces=nameSpaces).text if snpEffect.find('db:rs-id', namespaces=nameSpaces) is not None else None
        definingChange = snpEffect.find('db:defining-change', namespaces=nameSpaces).text if snpEffect.find('db:defining-change', namespaces=nameSpaces) is not None else None
        description = snpEffect.find('db:description', namespaces=nameSpaces).text if snpEffect.find('db:description', namespaces=nameSpaces) is not None else None
        pubmedID = snpEffect.find('db:pubmed-id', namespaces=nameSpaces).text if snpEffect.find('db:pubmed-id', namespaces=nameSpaces) is not None else None
        snps.append({
            'proteinName': proteinName,
            'geneSymbol': geneSymbol,
            'UniProtAC': UniProtID,
            'rsID': rsID,
            'definingChange': definingChange,
            'description': description,
            'PMID': pubmedID
        })

    # 靶标
    targets = tree.xpath("//db:drug/db:targets/db:target", namespaces=nameSpaces)
    drugTarget = []
    for target in targets:
        targetDBID = target.find('db:id', namespaces=nameSpaces).text if target.find('db:id', namespaces=nameSpaces) is not None else None
        targetName = target.find('db:name', namespaces=nameSpaces).text if target.find('db:name', namespaces=nameSpaces) is not None else None
        targetOrganism = target.find('db:organism', namespaces=nameSpaces).text if target.find('db:organism', namespaces=nameSpaces) is not None else None
        targetActions = [action.text for action in target.xpath("db:actions/db:action", namespaces=nameSpaces)]

        # 参考文献信息
        references = target.xpath("db:references/db:articles/db:article", namespaces=nameSpaces)
        targetRef = []
        for ref in references:
            pubmedID = ref.find('db:pubmed-id', namespaces=nameSpaces).text if ref.find('db:pubmed-id', namespaces=nameSpaces) is not None else None
            citation = ref.find('db:citation', namespaces=nameSpaces).text if ref.find('db:citation', namespaces=nameSpaces) is not None else None
            targetRef.append({
                'PMID': pubmedID, 
                'citation': citation
            })
        
        # 功能与细节
        functionOverview = target.find('db:polypeptide/db:general-function', namespaces=nameSpaces).text if target.find('db:polypeptide/db:general-function', namespaces=nameSpaces) is not None else None
        functionDetails = target.find('db:polypeptide/db:specific-function', namespaces=nameSpaces).text if target.find('db:polypeptide/db:specific-function', namespaces=nameSpaces) is not None else None
        
        # 基因和染色体位置
        geneName = target.find('db:polypeptide/db:gene-name', namespaces=nameSpaces).text if target.find('db:polypeptide/db:gene-name', namespaces=nameSpaces) is not None else None
        chromosome = target.find('db:polypeptide/db:chromosome-location', namespaces=nameSpaces).text if target.find('db:polypeptide/db:chromosome-location', namespaces=nameSpaces) is not None else None
        locus = target.find('db:polypeptide/db:locus', namespaces=nameSpaces).text if target.find('db:polypeptide/db:locus', namespaces=nameSpaces) is not None else None

        # 其他数据库中的标识符
        exIdentifiers = target.xpath("db:polypeptide/db:external-identifiers/db:external-identifier", namespaces=nameSpaces)
        targetIdentifiers = []
        for exIdentifier in exIdentifiers:
            resource = exIdentifier.find('db:resource', namespaces=nameSpaces).text if exIdentifier.find('db:resource', namespaces=nameSpaces) is not None else None
            identifier = exIdentifier.find('db:identifier', namespaces=nameSpaces).text if exIdentifier.find('db:identifier', namespaces=nameSpaces) is not None else None
            targetIdentifiers.append({
                'resource': resource,
                'identifier': identifier
            })

        # 氨基酸序列
        aminoAcidSequence = target.find('db:polypeptide/db:amino-acid-sequence', namespaces=nameSpaces).text if target.find('db:polypeptide/db:amino-acid-sequence', namespaces=nameSpaces) is not None else None
        # 基因序列
        geneSequence = target.find('db:polypeptide/db:gene-sequence', namespaces=nameSpaces).text if target.find('db:polypeptide/db:gene-sequence', namespaces=nameSpaces) is not None else None

        # pfams
        pfams = target.xpath("db:polypeptide/db:pfams/db:pfam", namespaces=nameSpaces)
        targetPfams = []
        for pfam in pfams:
            identifier = pfam.find('db:identifier', namespaces=nameSpaces).text if pfam.find('db:identifier', namespaces=nameSpaces) is not None else None
            name = pfam.find('db:name', namespaces=nameSpaces).text if pfam.find('db:name', namespaces=nameSpaces) is not None else None
            targetPfams.append({
                'identifier': identifier,
                'name': name
            })

        # GO
        goClassifiers = target.xpath("db:polypeptide/db:go-classifiers/db:go-classifier", namespaces=nameSpaces)
        targetGO = []
        for go in goClassifiers:
            category = go.find('db:category', namespaces=nameSpaces).text if go.find('db:category', namespaces=nameSpaces) is not None else None
            description = go.find('db:description', namespaces=nameSpaces).text if go.find('db:description', namespaces=nameSpaces) is not None else None
            targetGO.append({
                'category': category,
                'description': description
            })

        drugTarget.append({
            'id': targetDBID,
            'name': targetName,
            'organism': targetOrganism,
            'actions': targetActions,
            'references': targetRef,
            'function': functionOverview,
            'functionDetails': functionDetails,
            'chr': chromosome,
            'locus': locus,
            'identifiers': targetIdentifiers,
            'aminoAcidSequence': aminoAcidSequence,
            'geneSequence': geneSequence,
            'pfams': targetPfams,
            'GO': targetGO
        })

    allDrugs.append({
        'DrugBankID': drugbankId,
        'drugName': drugName,
        'description': description,
        'drugReferences': drugRefs,
        'indication': indication,
        'drugInteractions': drugInter,
        'calculatedProperties': calcProp,
        'drugExIdentifiers': drugIdentifiers,
        'SNP': snps,
        'targets': drugTarget,
    })
