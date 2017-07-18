# GATK WDL
# import "hc_scatter.wdl" as sub

task MakeOutputDir {
    String go
    String output_dir
    command {
        mkdir -p ${output_dir}
    }
    output {
        String out = output_dir
    }
    parameter_meta {
        output_dir: "The root directory for where all sample directories and ref index files will be deposited."
    }
}

task CheckIndex {
    String output_dir
    String ref_file
    String out_file = sub(ref_file, "\\.fa*$", ".dict")
    String seq_dict = "${output_dir}/${out_file}"
    command {
        python -c "import os; print ( '0' if os.path.isfile('${seq_dict}') else '1')"
    }
    output {
        Int retcode = read_int(stdout())
        String out = "${output_dir}/${ref_file}"
    }
    parameter_meta {
        output_dir: "The root directory for where all sample directories and ref index files will be deposited."
        ref_file: "The reference fasta file name (without the path)."
        out_file: "The seq dict filename must be generated and is used to construct seq_dict"
        seq_dict: "The sequence dictionary created by Picard CreateSequenceDictionary"
    }
}

task IndexReference {
    String ref_path
    String ref_file
    String picard
    String output_dir
    String out_file = sub(ref_file, "\\.fasta*$", ".dict")
    String seq_dict = "${output_dir}/${out_file}"
    String old_ref = "${ref_path}/${ref_file}"
    String ref = "${output_dir}/${ref_file}"
    command {
        source /broad/software/scripts/useuse
        cp ${old_ref} ${ref}
        use BWA
        bwa index ${ref}
        use Samtools
        samtools faidx ${ref}
        rm ${seq_dict}
        java -jar ${picard} CreateSequenceDictionary REFERENCE=${ref} O=${seq_dict}
    }
    output {
        String out = ref
    }
    parameter_meta {
        ref_path: "The file path to the directory containing the reference file."
        ref_file: "The name of the reference file (without the path)."
        picard: "The path to the picard executable jar file."
        output_dir: "The root directory for where all sample directories and ref index files will be deposited."
        out_file: "The seq dict filename must be generated and is used to construct seq_dict"
        seq_dict: "The sequence dictionary created by Picard CreateSequenceDictionary"
        old_ref: "The full path to the original reference file location."
        ref: "The absolute path of the reference file to be used by the workflow."
    }
}

task CreateIntervalsList {
    String ref
    Float interval_size
    String output_dir
    command {
        source /broad/software/scripts/useuse
        use Python-2.7
        python /cil/shed/apps/internal/IntervalsCreator/intervals_creator.py -r ${ref} \
        -i ${interval_size} > ${output_dir}/intervals.list
    }
    output{
        String out = "${output_dir}/intervals.list"
    }
    parameter_meta {
        ref: "The absolute path of the reference file to be used by the workflow."
        interval_size: "The size in gigabases that each interval should approximate."
        output_dir: "The root directory for where all sample directories and ref index files will be deposited."
    }
}

task MakeDir {
    String output_dir
    String sample_name
    command {
        mkdir -p ${output_dir}/${sample_name}
    }
    output {
        String out = "${output_dir}/${sample_name}/"
        String sample = sample_name
    }
    parameter_meta {
        output_dir: "The root directory for where all sample directories and ref index files will be deposited."
        sample_name: "The name of the sample as indicated by the 1st column of the gatk.samples_file json input."
    }
}

task GenerateFastqNames {
    String sample_dir
    String sample_name
    command {
        echo "GenerateFastqNames: ${sample_dir}/${sample_name}.1.fq, ${sample_dir}/${sample_name}.2.fq"
    }
    output {
        Array[String] fastq_out= ["${sample_dir}/${sample_name}.1.fq", "${sample_dir}/${sample_name}.2.fq"]
    }
    parameter_meta {
        sample_dir: "The sample-specific directory inside output_dir for each sample."
        sample_name: "The name of the sample as indicated by the 1st column of the gatk.samples_file json input."
    }
}

task SamToFastq {
    String picard
    String in_bam
    String sample_name
    String sample_dir
    String out_fq1 = "${sample_dir}/${sample_name}.1.fq"
    String out_fq2 = "${sample_dir}/${sample_name}.2.fq"
    command {
        java -Xmx12G -jar ${picard} SamToFastq INPUT=${in_bam} FASTQ=${out_fq1} SECOND_END_FASTQ=${out_fq2} VALIDATION_STRINGENCY=LENIENT
    }
    parameter_meta {
        picard: "The absolute path to the picard jar to execute."
        in_bam: "The bam file to convert to fastq."
        sample_dir: "The sample-specific directory inside output_dir for each sample."
        sample_name: "The name of the sample as indicated by the 1st column of the gatk.samples_file json input."
        out_fq1: "The fastq file containing the first read of each pair."
        out_fq2: "The fastq file containing the second read of each pair"
    }
}

task CopyFastq {
    String fq
    Int pair
    String sample_name
    String sample_dir
    String out_fq = "${sample_dir}/${sample_name}.${pair}.fq"
    command {
        cp ${fq} ${out_fq}
    }
    parameter_meta {
        fq: "The fastq file to copy."
        sample_dir: "The sample-specific directory inside output_dir for each sample."
        sample_name: "The name of the sample as indicated by the 1st column of the gatk.samples_file json input."
        out_fq: "the absolute path of the copied fastq file."
    }
}

task AlignBAM {
    String ref
    String sample_dir
    String sample_name
    Array[String] fq_array
    String read_group = "'@RG\\tID:FLOWCELL_${sample_name}\\tSM:${sample_name}\\tPL:ILLUMINA\\tLB:LIB_${sample_name}'"
    command {
        source /broad/software/scripts/useuse
        use BWA
        bwa mem -t 8 -R ${read_group} ${ref} ${fq_array[0]} ${fq_array[1]} > ${sample_dir}${sample_name}.aligned.sam
    }
    output {
        String aligned_sam = "${sample_dir}/${sample_name}.aligned.sam"
    }
    parameter_meta {
        ref: "fasta file of reference genome"
        sample_dir: "The sample-specific directory inside output_dir for each sample."
        sample_name: "The name of the sample as indicated by the 1st column of the gatk.samples_file json input."
        fq_array: "An array containing the paths to the first and second fastq files."
        read_group: "The read group string that will be included in the bam header."
    }
}

task SortSAM {
    String picard
    String aligned_sam
    String sample_dir
    String out_bam = sub(aligned_sam, "\\.sam*$", ".sorted.bam")
    command {
        source /broad/software/scripts/useuse
        use Java-1.8
        java -Xmx8G -jar ${picard} SortSam I=${aligned_sam} O=${out_bam} SO=coordinate
    }
    output {
        String bam = sub(aligned_sam, "\\.sam*$", ".sorted.bam")
    }
    parameter_meta {
        picard: "The absolute path to the picard jar to execute."
        aligned_sam: "The sam file to be sorted."
        sample_dir: "The sample-specific directory inside output_dir for each sample."
        out_bam: "The sorted bam file."
    }
}

task MarkDuplicates {
    String picard
    String sorted_bam
    String out_bam = sub(sorted_bam, "\\.bam*$", ".marked_duplicates.bam")
    String metrics = sub(sorted_bam, "\\.bam*$", ".marked_duplicates.metrics")
    command {
        source /broad/software/scripts/useuse
        use Java-1.8
        java -Xmx8G -jar ${picard} MarkDuplicates I=${sorted_bam} O=${out_bam} M=${metrics}
    }
    output {
        String bam = sub(sorted_bam, "\\.bam*$", ".marked_duplicates.bam")
    }
    parameter_meta {
        picard: "The absolute path to the picard jar to execute."
        sorted_bam: "The sorted bam file to mark duplicates on."
        out_bam: "The bam file where duplicates are marked."
        metrics: "The marked duplicates metrics file."
    }
}

task ReorderSAM {
    String picard
    String marked_bam
    String out_bam = sub(marked_bam, "\\.bam*$", ".reordered.bam")
    String ref
    command {
        source /broad/software/scripts/useuse
        use Java-1.8
        java -Xmx8G -jar ${picard} ReorderSam I=${marked_bam} O=${out_bam} R=${ref}
    }
    output {
        String bam = out_bam
    }
    parameter_meta {
        picard: "The absolute path to the picard jar to execute."
        marked_bam: "The bam file where duplicates are marked."
        out_bam: "The reordered bam file."
        ref: "fasta file of reference genome"
    }
}

task IndexBAM {
    String reordered_bam

    command {
        source /broad/software/scripts/useuse
        use Samtools
        samtools index ${reordered_bam}
    }
    output {
       String bam = reordered_bam
    }
    parameter_meta {
        reordered_bam: "the reordered bam file to be indexed."
    }
}

task RealignerTargetCreator {
    String gatk
    String ref
    String in_bam
    String out = sub(in_bam, "\\.bam*$", ".interval_list")
    command {
        source /broad/software/scripts/useuse
        use Java-1.8
        java -Xmx8G -jar ${gatk} -T RealignerTargetCreator -nct 1 -nt 24 -R ${ref} -I ${in_bam} -o ${out}
    }
    output {
        String intervals = out
    }
    parameter_meta {
        gatk: "The absolute path to the gatk executable jar."
        ref: "fasta file of reference genome"
        in_bam: "The input bam for the gatk task"
        out: "The intervals list to be used by IndelRealigner"
    }
}

task IndelRealigner {
    String gatk
    String ref
    String in_bam
    String intervals
    String out = sub(in_bam, "\\.bam*$", ".indels_realigned.bam")

    command {
        source /broad/software/scripts/useuse
        use Java-1.8
        java -Xmx4G -jar ${gatk} -T IndelRealigner -nct 1 -nt 1 -R ${ref} -I ${in_bam} -targetIntervals ${intervals} -o ${out}
    }
    output {
        String bam = out
    }

    parameter_meta {
        gatk: "The absolute path to the gatk executable jar."
        ref: "fasta file of reference genome"
        in_bam: "The input bam for the gatk task"
        intervals: "The intervals list to be used by IndelRealigner"
        out: "the bam including realigned indels."
    }
}

task CreateBamList {
    String samples_file
    String output_dir
    String out_file = "${output_dir}bqsr_bams_list.txt"
    command {
        cat ${samples_file} | cut -f 2 > ${out_file}
    }
    output {
        String out = out_file
    }
    parameter_meta {
        samples_file: "The text file containing sample names and bam file paths."
        output_dir: "The root directory for where all sample directories and ref index files will be deposited."
        out_file: "The text file containing absolute paths to all bam files, one per line."
    }
}

task BaseRecalibrator {
    String gatk
    String ref
    String sample_dir
    String bam
    Array[String] known_sites
    String ? bqsr
    String out_file
    command {
    java -Xmx4G  -jar ${gatk} -T BaseRecalibrator -nct 8 -nt 1 -R ${ref} -I  ${bam} -knownSites ${sep=" -knownSites " known_sites} -o ${sample_dir}/${out_file} ${" -BQSR " + bqsr}
    }
    output {
        String out = "${sample_dir}/${out_file}"

    }
    parameter_meta {
        gatk: "The absolute path to the gatk executable jar."
        ref: "fasta file of reference genome"
        bam_list: "The text file containing absolute paths to all bam files, one per line."
        known_sites: "An array of databases of known polymorphic sites."
        bqsr: "Full path to bqsr file."
    }
}

task AnalyzeCovariates {
    String gatk
    String ref
    String sample_name
    String sample_dir
    String before
    String after
    command {
    source /broad/software/scripts/useuse
    use R-3.1
    java -Xmx8G -jar ${gatk} \
      -T AnalyzeCovariates \
      -R ${ref} \
      -before ${before} \
      -after ${after} \
      -plots ${sample_dir}/recalibration_plots.pdf
    }
    parameter_meta {
        gatk: "The absolute path to the gatk executable jar."
        ref: "fasta file of reference genome"
        sample_dir: "The sample-specific directory inside output_dir for each sample."
        sample_name: "The name of the sample as indicated by the 1st column of the gatk.samples_file json input."
        known_sites: "An array of databases of known polymorphic sites."
        before: "The table output from the first BaseRecalibrator step."
        after: "The table output from the second BaseRecalibrator step."
    }
}

task PrintReads {
    String gatk
    String ref
    String in_bam
    String bqsr
    String out = sub(in_bam, "\\.bam*$", ".bqsr.bam")
    command {
        source /broad/software/scripts/useuse
        use Java-1.8
        java -Xmx4G -jar ${gatk} -T PrintReads -nct 8 -nt 1 -R ${ref} -I ${in_bam} -BQSR ${bqsr} -o ${out}
    }
    output {
        String bam = out
    }
    parameter_meta {
        gatk: "The absolute path to the gatk executable jar."
        ref: "fasta file of reference genome"
        in_bam: "The input bam for PrintReads."
        bqsr: "Full path to bqsr file."
        out: "The bam file with bqsr applied to it."
    }
}
# TODO: Make sure that the call mirrors logs of call in python pipeline.
# NOTE: HaplotypeCaller complains if I don't provide --variant_index_type and variant_index_parameter
task HaplotypeCaller {
    String gatk
	String ref
	String sample_name
	String sample_dir
	String in_bam
	String ? intervals
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
			${"--intervals " + intervals} \
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

task GenotypeGVCFs {
	String gatk
	String ref
	String ? extra_gg_params # If a parameter you'd like to use is missing from this task, use this term to add your own string
	String ? intervals
	Array[String] variant_files
    String output_dir
    String gcvf_out = "${output_dir}/genotypeGVCFs.vcf"
	command {
        source /broad/software/scripts/useuse
	    use Java-1.8
		java -Xmx8G -jar ${gatk} \
			-T GenotypeGVCFs \
			-R ${ref} \
			${sep=" --intervals " "--intervals " + intervals} \
			-o ${gcvf_out} \
			-V ${sep=" -V " variant_files} \
			${default="\n" extra_gg_params}
	}
	output {
		#To track additional outputs from your task, please manually add them below
		String out = gcvf_out
	}
	parameter_meta {
		gatk: "Executable jar for the GenomeAnalysisTK"
		ref: "fasta file of reference genome"
		extra_gg_params: "An optional parameter which allows the user to specify additions to the command line at run time"
		out: "File to which variants should be written"
		ploidy: "Ploidy (number of chromosomes) per sample. For pooled data, set to (Number of samples in each pool * Sample Ploidy)."
		variant_files: "One or more input gVCF files"
		intervals: "One or more genomic intervals over which to operate"
		gcvf_out: "The output vcf of GenotypeGVCFs"
	}
}

# https://software.broadinstitute.org/gatk/documentation/article.php?id=1259
task VariantRecalibrator {
	String gatk
	String ref
	String output_dir
	String mode
	String ? intervals
	String task_input
    Array[String] resource
    Array[String] annotation
    Int ? max_gaussians
    Int ? mq_cap
	String tranches_file = "${output_dir}/${mode}.tranches"
    String recal_file = "${output_dir}/${mode}.recal"
    String rscript_file = "${output_dir}/${mode}.plots.R"
	String ? extra_vr_params # If a parameter you'd like to use is missing from this task, use this term to add your own string
	command {
        source /broad/software/scripts/useuse
        use Java-1.8
		java -Xmx8G -jar ${gatk} \
			-T VariantRecalibrator \
			-R ${ref} \
			${default="" "--intervals " + intervals} \
			-input ${task_input} \
			-mode ${mode} \
            -resource:${sep=" -resource:" resource} \
			-recalFile ${recal_file} \
			-tranchesFile ${tranches_file} \
			-rscriptFile ${rscript_file} \
			-an ${sep=" -an " annotation} \
			--maxGaussians ${max_gaussians} \
			--MQCapForLogitJitterTransform ${mq_cap}
			${default="\n" extra_vr_params}
	}

	output {
		#To track additional outputs from your task, please manually add them below
		String out = task_input
		String tranches = tranches_file
		String recal = recal_file
		String rscript = rscript_file
	}

	parameter_meta {
		gatk: "Executable jar for the GenomeAnalysisTK"
		ref: "fasta file of reference genome"
		extra_vr_params: "An optional parameter which allows the user to specify additions to the command line at run time"
		aggregate: "Additional raw input variants to be used in building the model"
		task_input: "One or more VCFs of raw input variants to be recalibrated"
		recal_file: "The output recal file used by ApplyRecalibration"
		resource: "A list of sites for which to apply a prior probability of being correct but which aren't used by the algorithm (training and truth sets are required to run)"
		tranches_file: "The output tranches file used by ApplyRecalibration"
		intervals: "One or more genomic intervals over which to operate"
		mode: "The mode for recalibration (indel or snp)."
		annotation: "An array of annotations to use for calculations."
		max_gaussians: "Max number of Gaussians for the positive model"
		mq_cap: "Apply logit transform and jitter to MQ values"
        output_dir: "The root directory for where all sample directories and ref index files will be deposited."
	}
}

task ApplyRecalibration {
    String gatk
    String ref
    String vcf_in
    Float ts_filter
    String recal_file
    String tranches
    String mode
    String output_dir
    String vcf_out = "${output_dir}/${mode}.recalibrated.filtered.vcf"
    command {
        source /broad/software/scripts/useuse
        use Java-1.8
		java -Xmx8G -jar ${gatk} \
        -T ApplyRecalibration \
        -R ${ref} \
        -input ${vcf_in} \
        --ts_filter_level ${ts_filter} \
        -tranchesFile ${tranches} \
        -recalFile ${recal_file} \
        -mode ${mode} \
        -o ${vcf_out}
		}
    output {
        String out = vcf_out
    }
    parameter_meta {
		gatk: "Executable jar for the GenomeAnalysisTK"
		ref: "fasta file of reference genome"
		vcf_in: "The raw input variants to be recalibrated."
		ts_filter: "The truth sensitivity level at which to start filtering"
		recal_file: "The output recal file used by ApplyRecalibration"
		mode: "Recalibration mode to employ: 1.) SNP for recalibrating only SNPs (emitting indels untouched in the output VCF); 2.) INDEL for indels; and 3.) BOTH for recalibrating both SNPs and indels simultaneously."
        output_dir: "The root directory for where all sample directories and ref index files will be deposited."
        vcf_out: "The output filtered and recalibrated VCF file in which each variant is annotated with its VQSLOD value"
    }
}

# http://gatkforums.broadinstitute.org/gatk/discussion/2806/howto-apply-hard-filters-to-a-call-set
task SelectVariants {
    String gatk
    String ref
    String output_dir
    String vcf_in
    String mode
    command {
        source /broad/software/scripts/useuse
        use Java-1.8
        java -Xmx8G -jar ${gatk} \
        -T SelectVariants \
        -R ${ref} \
        -V ${vcf_in} \
        -selectType ${mode} \
        -o ${output_dir}/select${mode}.vcf
    }
    output {
        String out = "${output_dir}/select${mode}.vcf"
    }
    parameter_meta {
        gatk: "Executable jar for the GenomeAnalysisTK"
        ref: "fasta file of reference genome"
        output_dir: "The root directory for where all sample directories and ref index files will be deposited."
        vcf_in: "The input variants file."
        vcf_out: "The output variants file."
        }
}

task HardFiltration {
    String gatk
    String ref
    String output_dir
    String vcf_in
    String variant_type
    String vcf_out = "${output_dir}/filtered_${variant_type}.vcf"
    String filter_expression
    command {
        source /broad/software/scripts/useuse
        use Java-1.8
        java -Xmx8G -jar ${gatk} \
            -T VariantFiltration \
            -R ${ref} \
            -V ${vcf_in} \
            --filterExpression ${filter_expression} \
            --filterName "my_variant_filter" \
            -o ${vcf_out}
    }
    output {
        String out = vcf_out
    }
    parameter_meta {
        gatk: "Executable jar for the GenomeAnalysisTK"
        ref: "fasta file of reference genome"
        output_dir: "The root directory for where all sample directories and ref index files will be deposited."
        vcf_in: "The input variants file."
        vcf_out: "The output variants file."
        filter_expression: "The user-defined expressions to indicate which variants to filter."
    }
}

task CombineVariants {
    String gatk
    String output_dir
    String ref
    String vcf1
    String vcf2
    String outfile = "${output_dir}/filtered.combined.vcf"
    command {
         java -jar -Xmx8G ${gatk} \
           -T CombineVariants \
           -R ${ref} \
           --variant ${vcf1} \
           --variant ${vcf2} \
           -o ${outfile} \
           -genotypeMergeOptions UNIQUIFY
    }
    output {
        String out = outfile
    }
}

# Based on http://gatkforums.broadinstitute.org/gatk/discussion/50/adding-genomic-annotations-using-snpeff-and-variantannotator
task SnpEff {
    String vcf_in
    String output_dir
    String vcf_out = "${output_dir}/snpEff_out.vcf"
    String snpeff
    String snpeff_db
    String ? snpeff_extra_params
    command {
        source /broad/software/scripts/useuse
        use Java-1.8
        java -Xmx4G -jar ${snpeff} -v -ud 0 ${snpeff_db} ${vcf_in} ${snpeff_extra_params} > ${vcf_out}
    }
    output {
        String out = vcf_out
    }
    parameter_meta {
        output_dir: "The root directory for where all sample directories and ref index files will be deposited."
        vcf_in: "The input variants file."
        vcf_out: "The output variants file."
        snp_eff: "The path to the snpEff executable."
        snpeff_db: "The snpeff database to use."
        snpeff_extra_params: "A string for passing any additional parameters to snpeff."
    }
}

workflow gatk {
    # Initialize workflow
    # Global parameters
    String picard
    String gatk_3_7
    String gatk = gatk_3_7
    # TCIR Selection
    Boolean tcir
    # BQSR selection and relevant parameters
    Boolean bqsr
    Array[String] known_sites
    # HaplotypeCaller parameters
    Float interval_size
    String ? erc
    Int ? ploidy
    String ? extra_hc_params
    String ? bqsr_recal_report
    # GenotypeGVCF parameters
    String ? extra_gg_params
    # VQSR selection and relevant parameters
    Boolean vqsr
    Array[String] snp_resource
    Array[String] indel_resource
    Array[String] snp_annotation
    Array[String] indel_annotation
    Int ? snp_max_gaussians
    Int ? indel_max_gaussians
    Int ? mq_cap_snp
    Int ? mq_cap_indel
    Float ts_filter_snp
    Float ts_filter_indel
    String ? extra_vr_params
    # Hard filtration selection and relevant parameters
    Boolean variant_filtration
    String filter_expression
    # SNPEff selection and relevant parameters
    Boolean use_snpeff
    String snpeff
    String snpeff_db
    String ? snpeff_extra_params

    call VersionCheck{
        input:
        gatk = gatk
    }
    # Check's if index files exist(using .dict file as marker). Will always output path to localized reference
    # With assumption that it either exists or will be created by IndexReference.
    call MakeOutputDir {
        input:
        output_dir = output_dir
    }
    call CheckIndex {
        input:
        ref_file = ref_file,
        output_dir = MakeOutputDir.out
        }
    # CheckIndex retcode 1 means sequence dictionary .dict file doesn't exist and assumes all index files also
    # don't exist, therefore IndexReference will create them.
    if (CheckIndex.retcode == 1) {
        call IndexReference {
            input:
            ref_path = ref_path,
            ref_file = ref_file,
            picard = picard,
            output_dir = MakeOutputDir.out
        }
    }
    String int_ref = select_first([CheckIndex.out, IndexReference.out])
    call CreateIntervalsList {
        input:
        ref = int_ref,
        interval_size = interval_size,
        output_dir = MakeOutputDir.out
    }

    scatter(sample in read_tsv(samples_file)) {
        # Within specified output_dir, create a subdir using sample_name specified in 1st column of tsv file.
        call MakeDir as MakeSampleDir{
            input:
            output_dir = MakeOutputDir.out,
            sample_name = sample[0]
        }

        if (length(sample) == 2) {
            call SamToFastq {
                input:
                picard = picard,
                in_bam = sample[1],
                sample_name = sample[0],
                sample_dir = MakeSampleDir.out
            }
        }

        if (length(sample) == 3) {
            call CopyFastq as CopyFastq1 {
                input:
                fq = sample[1],
                pair = 1,
                sample_name = sample[0],
                sample_dir = MakeSampleDir.out
            }

            call CopyFastq as CopyFastq2 {
                input:
                fq = sample[2],
                pair = 2,
                sample_name = sample[0],
                sample_dir = MakeSampleDir.out
            }
        }

        # This is necessary to name the eventual output of SamToFastq/CopyFastq as we can't do this inside those
        # tasks due to the fact they exist in conditional statements.
        call GenerateFastqNames {
            input:
            sample_name = sample[0],
            sample_dir = MakeSampleDir.out
        }
        call AlignBAM {
            input:
            ref = CheckIndex.out,
            sample_dir = MakeSampleDir.out,
            sample_name = sample[0],
            fq_array = GenerateFastqNames.fastq_out
        }
        call SortSAM {
            input:
            picard = picard,
            aligned_sam = AlignBAM.aligned_sam,
            sample_dir = MakeSampleDir.out
        }
        call MarkDuplicates {
            input:
            picard = picard,
            sorted_bam = SortSAM.bam
        }
        call ReorderSAM {
            input:
            picard = picard,
            marked_bam = MarkDuplicates.bam,
            ref = CheckIndex.out
        }
        call IndexBAM {
            input:
            reordered_bam = ReorderSAM.bam
        }
        if (tcir == true) {
            call RealignerTargetCreator {
                input:
                gatk = gatk,
                ref = CheckIndex.out,
                in_bam = IndexBAM.bam
            }
            call IndelRealigner {
                input:
                gatk = gatk,
                ref = CheckIndex.out,
                in_bam = IndexBAM.bam,
                intervals = RealignerTargetCreator.intervals
            }
        }
        if (bqsr == true) {
            String bqsr_bam = select_first([ReorderSAM.bam, IndelRealigner.bam])
            call BaseRecalibrator as BaseRecal_1 {
                input:
                gatk = gatk,
                ref = CheckIndex.out,
                sample_dir = MakeSampleDir.out,
                bam = bqsr_bam,
                known_sites = known_sites,
                out_file = "recal_data.table"
            }

            call BaseRecalibrator as BaseRecal_2 {
                input:
                gatk = gatk,
                ref = CheckIndex.out,
                sample_dir = MakeSampleDir.out,
                bam = bqsr_bam,
                known_sites = known_sites,
                bqsr = BaseRecal_1.out,
                out_file = "post_recal_data.table"
            }

            call AnalyzeCovariates {
                input:
               gatk = gatk,
                ref = CheckIndex.out,
                sample_name = sample[0],
                sample_dir = MakeSampleDir.out,
                before = BaseRecal_1.out,
                after = BaseRecal_2.out
            }

            call PrintReads {
                input:
                gatk = gatk,
                ref = CheckIndex.out,
                in_bam = bqsr_bam,
                bqsr = BaseRecal_2.out
            }
        }

        String hc_bam = select_first([PrintReads.bam, IndelRealigner.bam, ReorderSAM.bam])
        #call sub.hc_scatter {
            #input:
            #intervals_file = CreateIntervalsList.out,
            #gatk = gatk,
            #ref = CheckIndex.out,
            #sample_name = sample[0],
            #sample_dir = MakeSampleDir.out,
            #in_bam = hc_bam,
            #bqsr_recal_report = bqsr_recal_report,
            #ploidy = ploidy,
            #erc = erc,
            #extra_hc_params = extra_hc_params
            #}
            #output {
            #    String hc_scatter_output = hc_scatter.out
            #}

        call HaplotypeCaller {
            input:
            gatk = gatk,
            ref = CheckIndex.out,
            sample_name = sample[0],
            sample_dir = MakeSampleDir.out,
            in_bam = hc_bam,
            intervals = CreateIntervalsList.out,
            bqsr_file = bqsr_recal_report,
            ploidy = ploidy,
            erc = erc,
            extra_hc_params = extra_hc_params
        }
    # Scatter block ends
    }

    call GenotypeGVCFs {
	    input:
        gatk = gatk,
        ref = CheckIndex.out,
        extra_gg_params = extra_gg_params,
        intervals = CreateIntervalsList.out,
        variant_files = HaplotypeCaller.vcf,
        output_dir = MakeOutputDir.out
    }
    if (vqsr == true) {
        call VariantRecalibrator as SnpRecalibration {
            input:
            gatk = gatk,
            ref = CheckIndex.out,
            output_dir = MakeOutputDir.out,
            intervals = CreateIntervalsList.out,
            task_input = GenotypeGVCFs.out,
            resource = snp_resource,
            annotation = snp_annotation,
            mode = "snp",
            max_gaussians = snp_max_gaussians,
            mq_cap = mq_cap_snp,
            extra_vr_params = extra_vr_params
        }

        call ApplyRecalibration as ApplySnpRecalibration {
            input:
            gatk = gatk,
            ref = CheckIndex.out,
            vcf_in = GenotypeGVCFs.out,
            ts_filter = ts_filter_snp,
            recal_file = SnpRecalibration.recal,
            tranches = SnpRecalibration.tranches,
            mode = "snp",
            output_dir = MakeOutputDir.out
        }
        call VariantRecalibrator as IndelRecalibration {
            input:
            gatk = gatk,
            ref = CheckIndex.out,
            output_dir = MakeOutputDir.out,
            intervals = CreateIntervalsList.out,
            task_input = ApplySnpRecalibration.out,
            resource = indel_resource,
            mode = "indel",
            max_gaussians = indel_max_gaussians,
            mq_cap = mq_cap_indel,
            annotation = indel_annotation,
            extra_vr_params = extra_vr_params
        }
        call ApplyRecalibration as ApplyIndelRecalibration {
            input:
            gatk = gatk,
            ref = CheckIndex.out,
            vcf_in = ApplySnpRecalibration.out,
            ts_filter = ts_filter_indel,
            recal_file = IndelRecalibration.recal,
            tranches = IndelRecalibration.tranches,
            mode = "indel",
            output_dir = MakeOutputDir.out
        }
    }
    if (variant_filtration == true) {
        String sv_vcf = select_first([ApplyIndelRecalibration.out, GenotypeGVCFs.out])
        call SelectVariants as SelectSnps{
            input:
            gatk = gatk,
            output_dir = MakeOutputDir.out,
            ref = CheckIndex.out,
            vcf_in = sv_vcf,
            mode = "SNP"
        }
        call HardFiltration as FilterSnps{
            input:
            gatk = gatk,
            ref = CheckIndex.out,
            output_dir = MakeOutputDir.out,
            vcf_in = SelectSnps.out,
            variant_type = "SNPs",
            filter_expression = filter_expression
        }
        call SelectVariants as SelectIndels{
            input:
            gatk = gatk,
            output_dir = MakeOutputDir.out,
            ref = CheckIndex.out,
            vcf_in = sv_vcf,
            mode = "INDEL"
        }
        call HardFiltration as FilterIndels{
            input:
            gatk = gatk,
            ref = CheckIndex.out,
            output_dir = MakeOutputDir.out,
            vcf_in = SelectIndels.out,
            variant_type = "INDELS",
            filter_expression = filter_expression
        }
        call CombineVariants {
            input:
                gatk = gatk,
                output_dir = MakeOutputDir.out,
                ref = CheckIndex.out,
                vcf1 = FilterSnps.out,
                vcf2 = FilterIndels.out
        }
        if (use_snpeff == true) {
            call SnpEff {
                input:
                vcf_in = CombineVariants.out,
                output_dir = MakeOutputDir.out,
                snpeff_db = snpeff_db,
                snpeff = snpeff,
                snpeff_extra_params = snpeff_extra_params
            }
        }
    }
}