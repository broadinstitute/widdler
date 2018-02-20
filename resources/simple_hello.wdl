task helloWorld {
    File infile
    String name
    String out = "hello_out.txt"
    Int sleep
 command {
    sleep ${sleep}
    echo "Writing to file..."
    date >> ${infile}
    echo Hello, ${name} >> ${infile}
    cp ${infile} ${out}
    } output {
    File outfile = "${out}"
    } runtime {
     docker : "gcr.io/btl-dockers/btl_gatk:1"
 }
}

workflow hello {
    File infile
    String name
    Int sleep
    String out
    call helloWorld {
    input:
        infile = infile,
        name = name,
        out = out,
        sleep = sleep
    }
}