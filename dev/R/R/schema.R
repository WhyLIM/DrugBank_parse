load_yaml_file <- function(path) {
  if (!file.exists(path)) {
    stop(sprintf("Schema file does not exist: %s", path), call. = FALSE)
  }
  value <- yaml::read_yaml(path)
  if (!is.list(value)) {
    stop(sprintf("Schema file is empty or invalid: %s", path), call. = FALSE)
  }
  value
}

load_drugbank_schema <- function(schema_dir = NULL) {
  base <- if (is.null(schema_dir)) default_schema_dir() else schema_dir
  tables <- load_yaml_file(file.path(base, "tables.yml"))
  fields <- load_yaml_file(file.path(base, "fields.yml"))

  list(
    version = as.integer(tables$version),
    tables = tables$tables,
    fields = fields$fields
  )
}

load_drugbank_profiles <- function(schema_dir = NULL) {
  base <- if (is.null(schema_dir)) default_schema_dir() else schema_dir
  load_yaml_file(file.path(base, "profiles.yml"))
}

resolve_modules <- function(profile = "core", modules = NULL, schema_dir = NULL) {
  profiles <- load_drugbank_profiles(schema_dir)
  known_profiles <- profiles$profiles
  known_modules <- profiles$modules

  if (!profile %in% names(known_profiles)) {
    stop(sprintf("Unknown profile: %s", profile), call. = FALSE)
  }

  selected <- if (is.null(modules)) known_profiles[[profile]]$modules else modules
  for (module in selected) {
    if (!module %in% names(known_modules)) {
      stop(sprintf("Unknown module: %s", module), call. = FALSE)
    }
  }
  selected
}

resolve_tables <- function(modules, schema_dir = NULL) {
  profiles <- load_drugbank_profiles(schema_dir)
  known_modules <- profiles$modules
  tables <- character()

  for (module in modules) {
    if (!module %in% names(known_modules)) {
      stop(sprintf("Unknown module: %s", module), call. = FALSE)
    }
    for (table in known_modules[[module]]$tables) {
      if (!table %in% tables) {
        tables <- c(tables, table)
      }
    }
  }
  tables
}
