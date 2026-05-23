align_table_columns <- function(df, columns) {
  for (column in columns) {
    if (!column %in% names(df)) {
      df[[column]] <- rep("", nrow(df))
    }
  }

  aligned <- df[columns]
  for (column in columns) {
    values <- aligned[[column]]
    values <- as.character(values)
    values[is.na(values)] <- ""
    aligned[[column]] <- values
  }

  rownames(aligned) <- NULL
  aligned
}

write_drugbank_tables <- function(result, outdir, schema_dir = NULL) {
  schema <- load_drugbank_schema(schema_dir)
  table_names <- names(result)
  schema_tables <- names(schema$tables)
  unknown_tables <- setdiff(table_names, schema_tables)

  if (length(unknown_tables) > 0) {
    stop(
      sprintf("Result contains unknown table(s): %s", paste(unknown_tables, collapse = ", ")),
      call. = FALSE
    )
  }

  dir.create(outdir, recursive = TRUE, showWarnings = FALSE)

  written <- character()
  for (table in table_names) {
    columns <- schema$tables[[table]]$columns
    aligned <- align_table_columns(result[[table]], columns)
    path <- file.path(outdir, paste0(table, ".csv"))
    write_csv_lines(aligned, path)
    written <- c(written, path)
  }

  written
}

write_csv_lines <- function(df, path) {
  lines <- c(
    paste(names(df), collapse = ","),
    apply(df, 1, function(row) paste(csv_escape(row), collapse = ","))
  )
  writeLines(lines, path, useBytes = TRUE)
}

csv_escape <- function(values) {
  values <- as.character(values)
  values[is.na(values)] <- ""
  needs_quote <- grepl("[\",\r\n]", values)
  values[needs_quote] <- paste0("\"", gsub("\"", "\"\"", values[needs_quote], fixed = TRUE), "\"")
  values
}
