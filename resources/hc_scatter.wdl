# Subworkflow for scattering HaplotypeCaller by intervals in intervals list file.

task HaplotypeCaller {
    String gatk
	String ref
	String sample_name
	String sample_dir
	String in_bam
	String interval
	String ? bqsr_file
	Int ? ploidy
	String ? erc
	String ? extra_hc_params
    String out = "${sample_dir}/${sample_name}.g.vcf"
	command {
        source /broad/software/scripts/useuse
	    use Java-1.8
		java -Xmx8G -jar ${gatk} \
			-T HaplotypeCaller \
			-nt 1 \
			-R ${ref} \
			--input_file ${in_bam} \
			${"--intervals " + interval} \
			${"-BQSR " + bqsr_file} \
			-ERC ${default="GVCF" erc} \
			-ploidy ${default="2" ploidy} \
			--interval_padding 100 \
			-o ${out} \
			-variant_index_type LINEAR \
			-variant_index_parameter 128000 \
            ${default="\n" extra_hc_params}
	}
	output {
		#To track additional outputs from your task, please manually add them below
		String vcf = out
	}
	parameter_meta {
		gatk: "Executable jar for the GenomeAnalysisTK"
		ref: "fasta file of reference genome"
        sample_name: "The name of the sample as indicated by the 1st column of the gatk.samples_file json input."
        sample_dir: "The sample-specific directory inside output_dir for each sample."
        in_bam: "The bam file to call HaplotypeCaller on."
        intervals: "An array of intervals to restrict processing to."
        bqsr_file: "The full path to the BQSR file."
        erc: "Mode for emitting reference confidence scores."
        extra_hc_params: "A parameter that allows users to pass any additional paramters to the task."
        out: "VCF file produced by haplotype caller."
	}
}

workflow hc_scatter {
    String gatk
	String ref
	String sample_name
	String sample_dir
	String in_bam
	String intervals
	String ? bqsr_file
	Int ? ploidy
	String ? erc
	String ? extra_hc_params

	scatter(interval in read_tsv(intervals)) {
	    call HaplotypeCaller {
	        input:
	        gatk = gatk,
	        ref = ref,
	        sample_dir = sample_dir,
	        in_bam = in_bam,
	        interval = interval[0],
	        bqsr_file = bqsr_file,
	        ploidy = ploidy,
	        erc = erc,
	        extra_hc_params = extra_hc_params
	    }
	}
}