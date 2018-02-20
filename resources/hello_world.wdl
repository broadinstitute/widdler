task helloWorld {
    File infile
    String name
    Int sleep
    command {
    sleep ${sleep}
    echo "Writing to file..."
    date >> ${infile}
    echo Hello, ${name} >> ${infile}
    } output {
    File outfile = "${infile}"
    } runtime {
     docker : "gcr.io/btl-dockers/btl_gatk:1"
 }
}


workflow hello {
    File infile
    File fofn
    String name
    Int sleep
    scatter(row in read_tsv(fofn)) {
        call helloWorld {
        input:
            infile = row[1],
            name = row[0],
            sleep = sleep
        }
    }
}