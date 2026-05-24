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

new_parse_accumulator <- function(tables) {
  stats::setNames(vector("list", length(tables)), tables)
}

append_accumulated_row <- function(result, table, row) {
  if (!table %in% names(result)) {
    stop(sprintf("Table is not enabled for this parse result: %s", table), call. = FALSE)
  }

  result[[table]][[length(result[[table]]) + 1L]] <- as.list(row)
  result
}

materialize_rows <- function(rows) {
  if (length(rows) == 0) {
    return(data.frame(stringsAsFactors = FALSE))
  }

  columns <- unique(unlist(lapply(rows, names), use.names = FALSE))
  data <- stats::setNames(vector("list", length(columns)), columns)

  for (column in columns) {
    data[[column]] <- vapply(
      rows,
      function(row) {
        value <- row[[column]]
        if (is.null(value) || length(value) == 0) {
          return(NA_character_)
        }
        as.character(value[[1]])
      },
      character(1)
    )
  }

  data.frame(data, stringsAsFactors = FALSE, check.names = FALSE)
}

materialize_parse_result <- function(result) {
  for (table in names(result)) {
    result[[table]] <- materialize_rows(result[[table]])
  }
  result
}
