 # @Author: Min Li
 # @Email: mli.bio@outlook.com
 # @Last Modified by: Min Li
 # @Timestamp for Last Modification: 2022-02-13 23:01:45
 # @Description: This R code file is used to obtain the final target_drug_indication form of DrugBank.

library(tidyverse)
setwd("D:/Study/Project/Graduation/1-1_deal_DrugBank")

rm(list = ls())
drugid_drugname <- read.delim("XML_dbid_dname.csv", header = T, sep = ",", stringsAsFactors = F, na.strings = c("", "\n"))
drugid_inchi <- read.delim("XML_dbid_inchi.csv", header = T, sep = ",", stringsAsFactors = F, na.strings = c("", "\n"))
drugid_indication <- read.delim("XML_dbid_indicati.csv", header = T, sep = ",", stringsAsFactors = F, na.strings = c("", "\n"))
targetid_drugid <- read.delim("XML_tgid_dbid.csv", header = T, sep = ",", check.names = F, stringsAsFactors = F, na.strings = c("", "\n"))
targetid_genename <- read.delim("XML_tgid_gname.csv", header = T, sep = ",", stringsAsFactors = F, na.strings = c("", "\n"))

targetid_drugid_single <- targetid_drugid[, 1:2]
names(targetid_drugid_single)[2] <- "DrugID"
for (i in 1:nrow(targetid_drugid)) {
  ndrug <- sum(!is.na(targetid_drugid[i, ])) - 1
  targetid_drugid_single[i, 2] <- paste(targetid_drugid[i, 2:(ndrug+1)], collapse = "; ")
}

DrugBank_TDI <- targetid_drugid_single %>% 
  tidyr::separate_rows(DrugID, sep = "; ") %>% 
  merge(drugid_drugname, by = "DrugID", all.x = T) %>% 
  merge(drugid_inchi, by = "DrugID", all.x = T) %>% 
  merge(drugid_indication, by = "DrugID", all.x = T) %>% 
  merge(targetid_genename, by = "UniprotAC", all.x = T) %>% 
  dplyr::select(c(1, 6, 2, 3, 4, 5))
DrugBank_TDI$Source <- "DrugBank"

write.csv(DrugBank_TDI, "DrugBank_TDI.csv", row.names = F)
