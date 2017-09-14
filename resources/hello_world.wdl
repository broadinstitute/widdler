task helloWorld {
    String name
 command {
    echo Hello, ${name}
    }
#    runtime {
#    backend: "Local"
#    }
}

workflow hello {
    String name
    call helloWorld {input: name = name}
}