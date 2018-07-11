task helloWorld {
    File infile
    String name
    String outfile = basename(infile)
    Int ? sleep
    Array[File] ? gs_url

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
    File ? optional_file
    command {
        cat ${input_file} > print_contents.txt
        more ${optional_file}
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
    File ? optional_file

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
        input: input_file = fofn, optional_file = optional_file
    }

    scatter(f in file_array) {
        call print_contents as pc2 {
            input: input_file = f
        }
    }

}