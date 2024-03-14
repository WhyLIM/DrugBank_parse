 # @Author: Min Li
 # @Email: mli.bio@outlook.com
 # @Last Modified by: Min Li
 # @Timestamp for Last Modification: 2024-03-14 11:29:00
 # @Description: This R code file is used to obtain the final target_drug_indication form of DrugBank.

library(tidyverse)
setwd("D:/Study/Project/DrugBank_parse/")

rm(list = ls())
drugid_drugname <- read.delim("XML_dbid_dname.csv", header = T, sep = ",", stringsAsFactors = F, na.strings = c("", "\n"))
drugid_inchi <- read.delim("XML_dbid_inchi.csv", header = T, sep = ",", stringsAsFactors = F, na.strings = c("", "\n"))
drugid_indication <- read.delim("XML_dbid_indicati.csv", header = T, sep = ",", stringsAsFactors = F, na.strings = c("", "\n"))
targetid_drugid <- read.delim("XML_tgid_dbid.csv", header = T, sep = ",", check.names = F, stringsAsFactors = F, na.strings = c("", "\n"))
targetid_genename <- read.delim("XML_tgid_gname.csv", header = T, sep = ",", stringsAsFactors = F, na.strings = c("", "\n"))

DrugBank_TDI <- targetid_drugid %>% 
  merge(drugid_drugname, by = "DrugID", all.x = T) %>% 
  merge(drugid_inchi, by = "DrugID", all.x = T) %>% 
  merge(drugid_indication, by = "DrugID", all.x = T) %>% 
  merge(targetid_genename, by = "TargetID", all.x = T) %>% 
  dplyr::select(c(1, 6, 2, 3, 4, 5))
DrugBank_TDI$Source <- "DrugBank"

write.csv(DrugBank_TDI, "DrugBank_TDI.csv", row.names = F)
