#!/usr/bin/env Rscript

library(reshape2)
library(optparse)

option_list = list(
  make_option(c("-i", "--input"), type="character", default=NULL, help="A path to a file to melt"),
  make_option(c("-o", "--output"), type="character", default=file.path(getwd(), "output.tabular"), help="A path to an output")
)
opt_parser = OptionParser(option_list=option_list)
opt = parse_args(opt_parser)

if (is.null(opt$input)) {
    print_help(opt_parser)
    stop("Please provide a path to an input file to melt (-i)", call.=FALSE)}


options(show.error.messages=F, error=function(){cat(geterrmessage(),file=stderr());q("no",1,F)})
loc <- Sys.setlocale("LC_MESSAGES", "en_US.UTF-8")
input <- read.csv(opt$input, sep='\t', header=TRUE)
cinput <- dcast(input, ... ~ variable)
write.table(cinput, opt$output, sep="\t", quote=FALSE, row.names=FALSE)
