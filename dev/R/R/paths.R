default_schema_dir <- function() {
  candidate <- file.path(getwd(), "..", "schema")
  if (dir.exists(candidate)) {
    return(normalizePath(candidate, winslash = "/", mustWork = TRUE))
  }

  candidate <- file.path(getwd(), "dev", "schema")
  if (dir.exists(candidate)) {
    return(normalizePath(candidate, winslash = "/", mustWork = TRUE))
  }

  stop("Cannot locate shared schema directory. Pass schema_dir explicitly.", call. = FALSE)
}
