drugbank_xml_ns <- function() {
  c(d = "http://www.drugbank.ca")
}

xml_text_first <- function(node, xpath) {
  found <- xml2::xml_find_first(node, xpath, ns = drugbank_xml_ns())
  if (inherits(found, "xml_missing")) {
    return("")
  }
  xml2::xml_text(found, trim = TRUE)
}

xml_attr_first <- function(node, xpath, attr) {
  found <- xml2::xml_find_first(node, xpath, ns = drugbank_xml_ns())
  if (inherits(found, "xml_missing")) {
    return("")
  }
  value <- xml2::xml_attr(found, attr)
  if (is.na(value)) "" else value
}

calculated_property <- function(drug_node, kind) {
  property_nodes <- xml2::xml_find_all(
    drug_node,
    "d:calculated-properties/d:property",
    ns = drugbank_xml_ns()
  )

  for (property_node in property_nodes) {
    if (identical(xml_text_first(property_node, "d:kind"), kind)) {
      return(xml_text_first(property_node, "d:value"))
    }
  }
  ""
}

parse_drugbank_xml <- function(path, profile = "core", modules = NULL, schema_dir = NULL) {
  if (!file.exists(path)) {
    stop(sprintf("Input XML file does not exist: %s", path), call. = FALSE)
  }

  selected_modules <- resolve_modules(
    profile = profile,
    modules = modules,
    schema_dir = schema_dir
  )
  tables <- resolve_tables(selected_modules, schema_dir = schema_dir)
  result <- new_parse_result(tables)

  if (length(tables) == 0) {
    return(unname(result))
  }

  # Fixture-sized fallback: this loads the XML tree. Restore streaming
  # xml_event_parse() before full DrugBank benchmarks.
  doc <- xml2::read_xml(path)
  drug_nodes <- xml2::xml_find_all(doc, "/d:drugbank/d:drug", ns = drugbank_xml_ns())

  if ("core" %in% selected_modules) {
    for (drug_node in drug_nodes) {
      result <- extract_core_drug(drug_node, result)
    }
  }

  deduplicate_table(result, "targets", key_fields = "target_id")
}

extract_core_drug <- function(drug_node, result) {
  drug_id <- xml_text_first(drug_node, "d:drugbank-id[@primary='true']")
  if (identical(drug_id, "")) {
    return(result)
  }

  drug_name <- xml_text_first(drug_node, "d:name")
  indication <- xml_text_first(drug_node, "d:indication")
  inchi <- calculated_property(drug_node, "InChI")

  result <- append_row(result, "drugs", list(
    drug_id = drug_id,
    drug_name = drug_name,
    inchi = inchi,
    source = "DrugBank"
  ))
  result <- append_row(result, "drug_indication", list(
    drug_id = drug_id,
    indication = indication,
    source = "DrugBank"
  ))

  target_nodes <- xml2::xml_find_all(drug_node, "d:targets/d:target", ns = drugbank_xml_ns())
  for (target_node in target_nodes) {
    target_id <- xml_attr_first(target_node, "d:polypeptide", "id")
    if (identical(target_id, "")) {
      next
    }

    target_name <- xml_text_first(target_node, "d:name")
    gene_name <- xml_text_first(target_node, "d:polypeptide/d:gene-name")
    organism <- xml_text_first(target_node, "d:organism")

    result <- append_row(result, "targets", list(
      target_id = target_id,
      target_name = target_name,
      gene_name = gene_name,
      organism = organism,
      source = "DrugBank"
    ))
    result <- append_row(result, "drug_target", list(
      drug_id = drug_id,
      target_id = target_id,
      source = "DrugBank"
    ))
    result <- append_row(result, "target_drug_indication", list(
      target_id = target_id,
      gene_name = gene_name,
      drug_id = drug_id,
      drug_name = drug_name,
      inchi = inchi,
      indication = indication,
      source = "DrugBank"
    ))
  }

  result
}

deduplicate_table <- function(result, table, key_fields) {
  if (!table %in% names(result) || nrow(result[[table]]) == 0) {
    return(result)
  }

  keys <- do.call(paste, c(result[[table]][key_fields], sep = "\r"))
  result[[table]] <- result[[table]][!duplicated(keys), , drop = FALSE]
  rownames(result[[table]]) <- NULL
  result
}
