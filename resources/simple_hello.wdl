task helloWorld {
    File infile
    String name
    String out = "hello_out.txt"
    Int ? sleep
 command {
    python -c "if ${sleep} == 1: print (${sleep})"
    sleep ${sleep}
    echo "Writing to file..."
    date >> ${infile}
    echo Hello, ${name} >> ${infile}
    cp ${infile} ${out}
    } output {
    File outfile = "${out}"
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