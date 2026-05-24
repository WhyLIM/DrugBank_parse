xml_text_first <- function(node, xpath) {
  values <- XML::xpathSApply(node, xpath, XML::xmlValue)
  if (length(values) == 0) {
    return("")
  }
  trimws(gsub("\r\n?", "\n", values[[1]]))
}

xml_attr_first <- function(node, xpath, attr) {
  found <- XML::getNodeSet(node, xpath)
  if (length(found) == 0) {
    return("")
  }
  value <- XML::xmlGetAttr(found[[1]], attr, default = "")
  if (is.na(value)) "" else value
}

calculated_property <- function(drug_node, kind) {
  property_nodes <- XML::getNodeSet(drug_node, "calculated-properties/property")

  for (property_node in property_nodes) {
    if (identical(xml_text_first(property_node, "kind"), kind)) {
      return(xml_text_first(property_node, "value"))
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

  if ("core" %in% selected_modules) {
    handle_drug <- function(drug_node, ...) {
      result <<- extract_core_drug(drug_node, result)
      FALSE
    }
    XML::xmlEventParse(
      path,
      branches = list(drug = handle_drug),
      useTagName = TRUE,
      addContext = FALSE,
      trim = FALSE
    )
  }

  deduplicate_table(result, "targets", key_fields = "target_id")
}

extract_core_drug <- function(drug_node, result) {
  drug_id <- xml_text_first(drug_node, "drugbank-id[@primary='true']")
  if (identical(drug_id, "")) {
    return(result)
  }

  drug_name <- xml_text_first(drug_node, "name")
  indication <- xml_text_first(drug_node, "indication")
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

  target_nodes <- XML::getNodeSet(drug_node, "targets/target")
  for (target_node in target_nodes) {
    target_id <- xml_attr_first(target_node, "polypeptide", "id")
    if (identical(target_id, "")) {
      next
    }

    target_name <- xml_text_first(target_node, "name")
    gene_name <- xml_text_first(target_node, "polypeptide/gene-name")
    organism <- xml_text_first(target_node, "organism")

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
