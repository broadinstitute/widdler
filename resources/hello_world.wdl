task helloWorld {
    String name
    String out
    Int ? sleep
 command {
    sleep $sleep
    echo Hello, ${name} > ${out}
    } output {
    File outfile = "${out}"
 } runtime {
     docker : "gcr.io/btl-dockers/btl_gatk:1"
 }
}

workflow hello {
    String name
    Int sleep
    String out
    call helloWorld {
    input:
        name = name,
        out = out,
        sleep = sleep
    }
}