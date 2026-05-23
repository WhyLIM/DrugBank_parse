test_that("new_parse_result initializes requested tables", {
  result <- new_parse_result(c("drugs", "targets"))

  expect_named(result, c("drugs", "targets"))
  expect_true(is.data.frame(result$drugs))
  expect_equal(nrow(result$drugs), 0)
})

test_that("append_row rejects tables outside selected profile", {
  result <- new_parse_result(c("drugs"))

  expect_error(
    append_row(result, "targets", list(target_id = "P00734")),
    "Table is not enabled"
  )
})

test_that("append_row appends first and second rows while preserving column order", {
  result <- new_parse_result(c("drugs"))

  result <- append_row(result, "drugs", list(drugbank_id = "DB00001", name = "Lepirudin"))
  result <- append_row(result, "drugs", list(drugbank_id = "DB00002", name = "Cetuximab", type = "biotech"))

  expect_named(result$drugs, c("drugbank_id", "name", "type"))
  expect_equal(nrow(result$drugs), 2)
  expect_equal(result$drugs$drugbank_id, c("DB00001", "DB00002"))
  expect_equal(result$drugs$name, c("Lepirudin", "Cetuximab"))
})

test_that("append_row fills missing fields with NA", {
  result <- new_parse_result(c("drugs"))

  result <- append_row(result, "drugs", list(drugbank_id = "DB00001", name = "Lepirudin"))
  result <- append_row(result, "drugs", list(drugbank_id = "DB00002"))

  expect_named(result$drugs, c("drugbank_id", "name"))
  expect_equal(result$drugs$name, c("Lepirudin", NA_character_))
})
