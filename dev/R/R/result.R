new_parse_result <- function(tables) {
  result <- stats::setNames(vector("list", length(tables)), tables)
  for (table in tables) {
    result[[table]] <- data.frame(stringsAsFactors = FALSE)
  }
  result
}

add_missing_columns <- function(df, columns) {
  for (column in columns) {
    if (!column %in% names(df)) {
      df[[column]] <- rep(NA_character_, nrow(df))
    }
  }
  df
}

append_row <- function(result, table, row) {
  if (!table %in% names(result)) {
    stop(sprintf("Table is not enabled for this parse result: %s", table), call. = FALSE)
  }

  row_df <- as.data.frame(row, stringsAsFactors = FALSE)
  existing_columns <- names(result[[table]])
  row_columns <- names(row_df)
  all_columns <- c(existing_columns, setdiff(row_columns, existing_columns))

  result[[table]] <- add_missing_columns(result[[table]], all_columns)
  row_df <- add_missing_columns(row_df, all_columns)
  result[[table]] <- rbind(result[[table]][all_columns], row_df[all_columns])
  rownames(result[[table]]) <- NULL
  result
}
