repo_root <- function() {
  normalizePath(file.path(testthat::test_path(), "..", "..", "..", ".."), winslash = "/", mustWork = TRUE)
}

fixture_xml <- function() {
  file.path(repo_root(), "test-database.xml")
}

shared_schema_dir <- function() {
  file.path(repo_root(), "dev", "schema")
}

expected_core_dir <- function() {
  file.path(repo_root(), "dev", "fixtures", "expected", "core")
}
