task helloWorld {
    String name
    command {
        python C:\Dev\Python\widdler>python widdler.py -h -u ${name}
    }
    }
workflow hello {
    String name

    call helloWorld{
    input:name=name
    }
}