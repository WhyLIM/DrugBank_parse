expected_core_files <- function() {
  c(
    "drugs.csv",
    "targets.csv",
    "drug_target.csv",
    "drug_indication.csv",
    "target_drug_indication.csv"
  )
}

test_that("write_drugbank_tables writes core CSVs with schema headers", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())
  outdir <- tempfile("drugbank-r-core-")
  dir.create(outdir)

  written <- write_drugbank_tables(result, outdir, schema_dir = shared_schema_dir())

  expect_equal(sort(basename(written)), sort(expected_core_files()))
  header <- readLines(file.path(outdir, "drugs.csv"), n = 1)
  expect_equal(header, "drug_id,drug_name,inchi,source")
})

test_that("R exported core CSVs match shared expected fixture files", {
  result <- parse_drugbank_xml(fixture_xml(), schema_dir = shared_schema_dir())
  outdir <- tempfile("drugbank-r-core-")
  dir.create(outdir)

  write_drugbank_tables(result, outdir, schema_dir = shared_schema_dir())

  expected_dir <- expected_core_dir()
  expect_true(dir.exists(expected_dir))
  expect_equal(sort(list.files(expected_dir, pattern = "\\.csv$")), sort(expected_core_files()))
  expect_equal(sort(list.files(outdir, pattern = "\\.csv$")), sort(expected_core_files()))

  for (filename in expected_core_files()) {
    expect_equal(
      readLines(file.path(outdir, filename), warn = FALSE),
      readLines(file.path(expected_dir, filename), warn = FALSE),
      info = filename
    )
  }
})
