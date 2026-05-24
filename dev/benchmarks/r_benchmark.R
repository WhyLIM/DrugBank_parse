script_path <- function() {
  file_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
  if (length(file_arg) > 0) {
    return(normalizePath(sub("^--file=", "", file_arg[[1]]), winslash = "/", mustWork = TRUE))
  }
  normalizePath(file.path(getwd(), "r_benchmark.R"), winslash = "/", mustWork = FALSE)
}

parse_args <- function(args) {
  values <- list(profile = "core")
  i <- 1
  while (i <= length(args)) {
    key <- args[[i]]
    if (!startsWith(key, "--")) {
      stop(sprintf("Unexpected argument: %s", key), call. = FALSE)
    }
    if (i == length(args)) {
      stop(sprintf("Missing value for argument: %s", key), call. = FALSE)
    }
    values[[substring(key, 3)]] <- args[[i + 1]]
    i <- i + 2
  }
  for (required in c("input", "outdir", "metrics")) {
    if (is.null(values[[required]])) {
      stop(sprintf("Missing required argument: --%s", required), call. = FALSE)
    }
  }
  values
}

json_escape <- function(value) {
  value <- gsub("\\", "\\\\", value, fixed = TRUE)
  value <- gsub("\"", "\\\"", value, fixed = TRUE)
  value <- gsub("\r", "\\r", value, fixed = TRUE)
  value <- gsub("\n", "\\n", value, fixed = TRUE)
  value
}

write_metrics_json <- function(metrics, path) {
  rows <- metrics$table_rows
  row_lines <- sprintf(
    "    \"%s\": %s",
    json_escape(names(rows)),
    as.integer(rows)
  )
  files <- sprintf("    \"%s\"", json_escape(metrics$written_files))
  lines <- c(
    "{",
    sprintf("  \"implementation\": \"%s\",", metrics$implementation),
    sprintf("  \"input_path\": \"%s\",", json_escape(metrics$input_path)),
    sprintf("  \"profile\": \"%s\",", json_escape(metrics$profile)),
    sprintf("  \"output_dir\": \"%s\",", json_escape(metrics$output_dir)),
    sprintf("  \"elapsed_seconds\": %.6f,", metrics$elapsed_seconds),
    "  \"table_rows\": {",
    paste(row_lines, collapse = ",\n"),
    "  },",
    "  \"written_files\": [",
    paste(files, collapse = ",\n"),
    "  ]",
    "}"
  )
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  writeLines(lines, path, useBytes = TRUE)
}

load_local_package <- function() {
  benchmark_dir <- dirname(script_path())
  package_dir <- normalizePath(file.path(benchmark_dir, "..", "R"), winslash = "/", mustWork = TRUE)
  if (!requireNamespace("pkgload", quietly = TRUE)) {
    stop("Package 'pkgload' is required to load the local R package.", call. = FALSE)
  }
  pkgload::load_all(package_dir, quiet = TRUE)
}

run_benchmark <- function(input_path, outdir, metrics_path, profile = "core") {
  load_local_package()
  start <- proc.time()[["elapsed"]]
  result <- parse_drugbank_xml(input_path, profile = profile, schema_dir = "../schema")
  written <- write_drugbank_tables(result, outdir, schema_dir = "../schema")
  elapsed <- proc.time()[["elapsed"]] - start

  metrics <- list(
    implementation = "r",
    input_path = input_path,
    profile = profile,
    output_dir = outdir,
    elapsed_seconds = elapsed,
    table_rows = vapply(result, nrow, integer(1)),
    written_files = basename(written)
  )
  write_metrics_json(metrics, metrics_path)
  metrics
}

args <- parse_args(commandArgs(trailingOnly = TRUE))
metrics <- run_benchmark(
  input_path = args$input,
  outdir = args$outdir,
  metrics_path = args$metrics,
  profile = args$profile
)
print(metrics)
