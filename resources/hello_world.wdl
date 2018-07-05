task helloWorld {
    String name
 command {
    echo Hello, ${name}
    }
    runtime {
		docker : "gcr.io/btl-dockers/btl_gatk:1"
    }
}

workflow hello {
    String name
    call helloWorld {input: name = name}
}