# This script was created to read RLID databases
# By Dongmei Chen (dchen@lcog.org)
# On October 30th, 2020

library(RODBC)
ReadFromSQL <- function(database='RLID', table='SALES'){
  dbhandle <- odbcDriverConnect(paste0('driver={SQL Server};server=rliddb.int.lcog.org,5433;database=',
                                       database, ';trusted_connection=true'))
  print(dbhandle)
  currTableSQL <- paste0("SELECT * From ", table)
  currTableDF <- sqlQuery(dbhandle, currTableSQL)
  odbcCloseAll()
  return(currTableDF)
}

# check number of records, records with one account and one taxlot
sales <- ReadFromSQL()
valid.sales <- sales[sales$arms_length == 'Y',]
print(paste0('There are ', dim(sales)[1], ' records in RLID sales', ', but only ',
            round(dim(valid.sales)[1]/dim(sales)[1]*100, 2),
            '% of the records are valid.'))
# There are 603990 records in RLID sales, 
# but only 42.17% of the records are valid.

head(valid.sales)
single.acct.sales <- valid.sales[valid.sales$multiple_account_flag == 'N',]
print(paste0('There are ', dim(valid.sales)[1], ' records of valid RLID sales', ', and ',
             round(dim(single.acct.sales)[1]/dim(valid.sales)[1]*100, 2),
             '% of the records are under a single account.'))
# There are 254712 records of valid RLID sales, 
# and 92.26% of the records are under a single account.

unique.taxlot.sales <- single.acct.sales[!duplicated(single.acct.sales$maplot),]
print(paste0('There are ', dim(single.acct.sales)[1], ' records of single account sales', ', but only ',
             round(dim(unique.taxlot.sales)[1]/dim(single.acct.sales)[1]*100, 2),
             '% of the records are single sales by taxlot.'))
# There are 235001 records of single account sales, 
# but only 31.12% of the records are single sales by taxlot.

comp.sales <- ReadFromSQL(database = 'RLID_WebApp_V3', 
                          table = 'WEBAPP_COMP_SALES_COMP')

dim(comp.sales)
unique.taxlot.comp.sales <- comp.sales[!duplicated(comp.sales$maplot),]

# merge by maplot

data <- merge(unique.taxlot.sales, unique.taxlot.comp.sales, 
              by='maplot')
data_new <- data[, colSums(is.na(data)) < nrow(data)]
outfolder <- 'C:/Users/clid1852/OneDrive - lanecouncilofgovernments/RLID/'
write.csv(data_new, paste0(outfolder, 'RLID_sales.csv'), 
          row.names = FALSE)
