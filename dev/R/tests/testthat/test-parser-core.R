test_that("parse_core_result_contains_expected_tables", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())

  expect_named(result, c(
    "drugs",
    "targets",
    "drug_target",
    "drug_indication",
    "target_drug_indication"
  ))
})

test_that("parse_with_empty_modules_does_not_emit_core_tables", {
  result <- parse_drugbank_xml(
    fixture_xml(),
    modules = character(),
    schema_dir = shared_schema_dir()
  )

  expect_equal(result, list())
})

test_that("parse_core_extracts_first_drug", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())

  drugs <- result$drugs
  expect_equal(nrow(drugs), 2)
  expect_equal(drugs$drug_id[1], "DB00001")
  expect_equal(drugs$drug_name[1], "Lepirudin")
  expect_equal(drugs$source[1], "DrugBank")
})

test_that("parse_core_extracts_target_relationships", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())

  drug_targets <- result$drug_target
  expect_equal(nrow(drug_targets), 3)
  expect_equal(
    paste(drug_targets$drug_id, drug_targets$target_id, sep = "->"),
    c("DB00001->P00734", "DB00014->P22888", "DB00014->P30968")
  )
})

test_that("parse_core_builds_denormalized_tdi", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())

  rows <- result$target_drug_indication
  expect_equal(nrow(rows), 3)
  expect_equal(
    paste(rows$drug_id, rows$target_id, sep = "->"),
    c("DB00001->P00734", "DB00014->P22888", "DB00014->P30968")
  )

  first <- rows[1, ]
  expect_equal(first$drug_id, "DB00001")
  expect_equal(first$drug_name, "Lepirudin")
  expect_false(grepl("Lepirudin", first$target_id, fixed = TRUE))

  db00014_rows <- rows[rows$drug_id == "DB00014", ]
  names_by_target <- stats::setNames(db00014_rows$drug_name, db00014_rows$target_id)
  genes_by_target <- stats::setNames(db00014_rows$gene_name, db00014_rows$target_id)

  expect_equal(unique(names_by_target), "Goserelin")
  expect_equal(genes_by_target[["P22888"]], "LHCGR")
  expect_equal(genes_by_target[["P30968"]], "GNRHR")
})

test_that("missing_input_file_fails_clearly", {
  missing <- file.path(tempdir(), "missing.xml")

  expect_error(
    parse_drugbank_xml(missing, schema_dir = shared_schema_dir()),
    "Input XML file does not exist"
  )
})
