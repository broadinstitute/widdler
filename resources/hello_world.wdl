task helloWorld {
    File infile
    String name
    String outfile = basename(infile)
    Int sleep
    command {
    sleep ${sleep}
    echo "Writing to file..."
    date >> ${outfile}
    echo Hello, ${name} >> ${outfile}
    } output {
    File output_file = "${outfile}"
    } runtime {
     docker : "gcr.io/btl-dockers/btl_gatk:1"
 }
}

task print_contents {
    File input_file
    command {
        cat ${input_file} > print_contents.txt
    } output {
    File outfile = "print_contents.txt"
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
    call print_contents {input: input_file = fofn}
}