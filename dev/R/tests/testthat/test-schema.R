test_that("load_drugbank_schema reads shared core tables", {
  schema <- load_drugbank_schema(shared_schema_dir())

  expect_equal(schema$version, 1)
  expect_equal(names(schema$tables), c(
    "drugs",
    "targets",
    "drug_target",
    "drug_indication",
    "target_drug_indication"
  ))
  expect_equal(schema$tables$drugs$columns, c("drug_id", "drug_name", "inchi", "source"))
})

test_that("resolve_modules reads core profile", {
  expect_equal(resolve_modules(profile = "core", modules = NULL, schema_dir = shared_schema_dir()), "core")
  expect_equal(resolve_modules(profile = "core", modules = c("core"), schema_dir = shared_schema_dir()), "core")
})

test_that("resolve_modules rejects unknown profile and module", {
  expect_error(resolve_modules(profile = "missing", schema_dir = shared_schema_dir()), "Unknown profile")
  expect_error(resolve_modules(profile = "core", modules = c("missing"), schema_dir = shared_schema_dir()), "Unknown module")
})

test_that("resolve_tables preserves core table order", {
  expect_equal(resolve_tables(c("core"), schema_dir = shared_schema_dir()), c(
    "drugs",
    "targets",
    "drug_target",
    "drug_indication",
    "target_drug_indication"
  ))
})
