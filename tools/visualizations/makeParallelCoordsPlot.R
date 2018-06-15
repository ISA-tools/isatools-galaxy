#!/usr/bin/env Rscript

library(data.table)
library(jsonlite)
# remove this line once r-ggparallel becomes available in conda
install.packages("ggparallel", repos="http://cran.uk.r-project.org")
library(ggparallel)
library(optparse)

# parse parameters
option_list = list(
  make_option(c("-s", "--study"), type="character", default=NULL, help="MetaboLights Study", metavar="character"),
  make_option(c("-i", "--isaFactorsJSON"), type="character", default=NULL, help="A path to an ISA Factor JSON"),
  make_option(c("-o", "--outputPath"), type="character", default=getwd(), help="Set output path for result files")
)
opt_parser = OptionParser(option_list=option_list)
opt = parse_args(opt_parser)

if (is.null(opt$study) && is.null(opt$isaFactorsJSON)){
  print_help(opt_parser)
  stop("Please provide a MetaboLights study (-s) or a ISA-tab directory (-i)", call.=FALSE)
}

study<-NULL
# download the data
if (!is.null(opt$study)) {
  mtbls_id <- opt$study
  output_path <- opt$outputPath
      ftp_path <- "ftp://ftp.ebi.ac.uk/pub/databases/metabolights/derived/parallel_coordinates/"
  json_file_path <- paste(output_path,"study_pc.json",sep="/")
  download.file(paste(ftp_path,mtbls_id,".json",sep=""),destfile = json_file_path)
  study <- fromJSON(json_file_path)
} else if(!is.null(opt$isaFactorsJSON)) {
  study <- fromJSON(opt$isaFactorsJSON)
}

colnames(study)[! colnames(study) %in% c("name", "files", "mafFile", "id", "metabolites")]->factors_no_name

if(is.null(factors_no_name)) {
  stop(paste("The MetaboLights study provided seems to have no factors, please contact the MetaboLights database referencing study ",mtbls_id,".",sep=""))
}

study.dt<-data.table(study,key = factors_no_name)
study.dt[, c("files","mafFile", "id"):=NULL]
study.dt[,list(Frequency = .N),by=factors_no_name]->study.dt.summary

sober_theme <- theme(axis.line=element_blank(),
      axis.ticks=element_blank(),
      legend.position="none",
      panel.background=element_blank(),
      panel.border=element_blank(),
      panel.grid.major=element_blank(),
      panel.grid.major.y=element_line(size = 0.3, colour = "grey", linetype = "dotted"),
      panel.grid.minor=element_blank(),
      plot.background=element_blank())

pdf_output <- paste( opt$outputPath, "factors_plot.pdf", sep="/")
pdf(file = pdf_output, paper = "a4r")

if(length(factors_no_name)==1)
{
  # if only one factor, then use stacked bar plot, otherwise, ggparallel
  study.dt.summary[,posStack := cumsum(Frequency) - Frequency/2,]
  ggplot(study.dt.summary, aes(colnames(study.dt.summary)[1],y=Frequency)) -> g
  g + geom_bar(aes(fill=study.dt.summary[[1]]), stat = "identity", position=position_stack(reverse = TRUE)) +
    labs(x="Factor") + geom_text(aes(label=study.dt.summary[[1]],y=posStack),colour="white",fontface="bold") + sober_theme
} else {
  ggparallel(study.dt.summary, vars = list(factors_no_name), weight = "Frequency", text.angle = 0) + sober_theme
}

dev.off()

table_output <- paste( opt$outputPath, "factors_table.tab", sep="/")
write.table(study.dt.summary, sep = "\t", row.names = FALSE, file = table_output)