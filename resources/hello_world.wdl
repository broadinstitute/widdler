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
    }
    output {
        File output_file = "${outfile}"
    }
    runtime {
        docker : "gcr.io/btl-dockers/btl_gatk:1"
    }
}

task print_contents {
    File input_file

    command {
        cat ${input_file} > print_contents.txt
    }
    output {
        File outfile = "print_contents.txt"
    }
    runtime {
        docker : "gcr.io/btl-dockers/btl_gatk:1"
    }
}


workflow hello {
    File fofn
    String name
    Int sleep
    Array[File] file_array

    String onprem_download_path = "/cil/shed/resources/jenkins_tests/"

    Map[String, String] handoff_files = {
        "helloWorld.output_file": "",
        "print_contents.outfile": "print_relabeled.txt"
    }

    scatter(row in read_tsv(fofn)) {
        call helloWorld {
        input:
            name = row[0],
            infile = row[1],
            sleep = sleep
        }
    }

    call print_contents {
        input: input_file = fofn
    }

    scatter(f in file_array) {
        call print_contents as pc2 {
            input: input_file = f
        }
    }

}