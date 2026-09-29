---
title: "From variant scores to a disease explanation"
subtitle: "MVA Hackathon 2026 · Track 1"
author: "Kaavin Prasanna"
date: "September 2026"
geometry: margin=0.8in
fontsize: 10pt
header-includes:
  - '\usepackage{needspace}'
  - '\let\originalsection\section'
  - '\renewcommand{\section}{\Needspace{6\baselineskip}\originalsection}'
---

# My conclusion

My leading candidate is a pair of BUB1B variants: **chr15:40209701 T>G** and **chr15:40220612 T>G**. The first is a stop-gain, p.Leu737Ter, with a ClinVar pathogenic/likely-pathogenic annotation. The second, p.Asn1002Lys, is a rare missense variant that remains a variant of uncertain significance. Together they form a plausible recessive explanation for mosaic variegated aneuploidy (MVA), but their phase is unresolved. I am submitting a candidate explanation, not a confirmed diagnosis.

The most important decision in my analysis came after the automated ranking. Exomiser gave a higher combined score to a single BUB1B allele associated with **somatic colorectal cancer** than to the recessive pair associated with **MVA**. I reviewed that difference rather than accepting the larger number as the better answer. My final ranking prioritizes the disease mechanism relevant to this case and records exactly how that decision changes the automated result.

**Submitter:** `kaavinp` · **Method:** `exomiser15-context-review`

**Code and submission files:** [kaapra081/mva-track1-kaavinp](https://github.com/kaapra081/mva-track1-kaavinp)

# What I contributed

I combined an established prioritization tool with a review process that makes its consequential decisions visible. Three parts matter most:

- **A broad starting point.** I ran Exomiser across the complete supplied VCF under a coding/splice-oriented configuration, then inventoried all 421 contributing genotype models. The automated search was not limited to a short list of MVA genes.
- **Disease context at the model level.** I compared the singleton and paired explanations, including their inheritance modes and disease annotations. Finding the right gene was not enough: the submitted hypothesis also needed to represent the relevant allele combination and mechanism.
- **A checkable path to the final CSV.** I kept the original output, encoded my review decisions in a versioned policy, and verified that every submitted allele was present in the source VCF and matched the reference. The export can be regenerated from the frozen results without repeating the analysis.

This is a practical, case-specific contribution. I did not develop a new pathogenicity predictor or establish that this review policy outperforms existing methods on other cases. Its value here is that the final answer can be traced through the automated scores, the biological judgment and the exported alleles.

# How I ran the analysis

I used the authorized single-sample GRCh38 VCF and seven proband HPO terms grounded in the clinical document. I kept family history separate from the child's phenotype observations. The sequencing sample was mapped to `PROBAND01` for submission; the input VCF was not rewritten. Raw genomic files and the clinical document remain outside the repository.

I ran **Exomiser 15.1.0**, **Java 21**, and the **2602 GRCh38 and phenotype resources**. The exact settings are in `config/analysis.yml`. The analysis used `PASS_ONLY` with gene blacklist, failed-variant, allele-balance, consequence, frequency and inheritance filters, followed by OMIM and HiPhive prioritization. HiPhive used the configured human, mouse, fish and network information. I retained the pathogenicity setting `keepNonPathogenic: true` so that this step did not itself discard variants solely on prediction status.

Frequency sources were UK10K and the configured gnomAD exome/genome populations. Prediction sources were REVEL, MVP, AlphaMissense and SpliceAI. I interpreted frequencies in Exomiser's units and kept missing frequency information distinct from a verified absence in population data. I did not infer parental segregation or de novo status from a singleton VCF.

The run processed **5,012,204 VCF records** into **4,962,047 single-allele variants**. After variant filtering, 1,011 remained; inheritance filtering left 589 variants across 364 analyzed genes. These produced the 421 contributing models used in my review.

| Sequential filter | Passed | Failed at this step |
|---|---:|---:|
| Gene blacklist | 4,933,759 | 28,288 |
| Failed-variant filter | 4,701,716 | 232,043 |
| Allele balance | 4,497,268 | 204,448 |
| Variant effect | 23,931 | 4,473,337 |
| Frequency | 1,011 | 22,920 |
| Pathogenicity | 1,011 | 0 |
| Inheritance | 589 | 422 |

The successful process took **80.11 seconds**, with peak observed process-tree RSS of **936,720 KiB**. That measures this run only; it is not a claim about performance on larger datasets. I resolved the recorded startup/configuration errors before the completed analysis and reused its outputs for the subsequent review and packaging.

# Why I ranked the BUB1B pair first

| Native hypothesis | Compatible disease context | Combined score | Phenotype score |
|---|---|---:|---:|
| BUB1B dominant singleton | Colorectal cancer, somatic | 0.544692 | 0.546282 |
| BUB1B recessive pair | MVA / MVA syndrome 1 | 0.485305 | 0.764649 |

A somatic cancer association is not, by itself, an explanation for a constitutional MVA presentation. The pair had the relevant MVA disease matches and the stronger native phenotype score. The combination of a disease-associated stop-gain and a rare second allele therefore warranted prioritization as a recessive hypothesis. That is the basis for my decision—not a claim that two heterozygous calls establish trans phase.

I made this decision after reviewing the native results and encoded it explicitly in `config/adjudication.json`. The policy names the BUB1B recessive MVA model and excludes the BUB1B somatic-colorectal singleton. It is **manual case adjudication**, not an unchanged Exomiser ranking or a general-purpose discovery rule.

For alternatives, I retained models with at least one native compatible-disease annotation and sorted them globally by combined score, phenotype score, variant score, gene, inheritance mode and allele identity. I removed duplicate allele-set hypotheses before selecting ten rows. Models lacking a compatible-disease annotation stay in the local inventory; excluding them from this shortlist does not establish that they are biologically impossible. Nor does retaining an alternative establish that it explains the case.

The original export had followed JSON model-emission order. I replaced that with the explicit review policy and stable sorting described above. EPCR is `1 - (rank - 1)/11`, used solely to encode my final order. **An EPCR of 1.0 is not a claim of diagnostic certainty.**

# My submitted hypotheses

| Rank | Gene | Exact GRCh38 allele(s) | EPCR |
|---:|---|---|---:|
| 1 | BUB1B | chr15:40209701 T>G; chr15:40220612 T>G | 1.000000 |
| 2 | FANCD2 | chr3:10046723 AG>A; chr3:10046725 TAAG>T | 0.909091 |
| 3 | HK1 | chr10:69315762 A>G | 0.818182 |
| 4 | LZTR1 | chr22:20996720 C>G | 0.727273 |
| 5 | SERPINA1 | chr14:94379487 CCT>C; chr14:94379492 G>GAC | 0.636364 |
| 6 | COL7A1 | chr3:48584547 C>T | 0.545455 |
| 7 | SH3BP2 | chr4:2827654 C>T | 0.454545 |
| 8 | ESR1 | chr6:151842246 A>G | 0.363636 |
| 9 | RBMX | chrX:136874347 C>G | 0.272727 |
| 10 | MBTPS1 | chr16:84070041 A>G | 0.181818 |

The secondary rows are alternatives for further review, not clinically reportable incidental findings. Each pair preserves native Exomiser model membership, but phase remains unresolved. The BUB1B missense allele remains a VUS, and computational support does not establish its functional effect. The available phenotype matches also do not explain every observation equally well.

# Checks I completed

I regenerated the final CSV from the frozen native output and confirmed that its bytes matched the reviewed submission. I separately checked all **13 unique exported alleles** against the indexed source VCF and GRCh38 reference: each had one exact matching record, a carried alternate allele, an explicit PASS filter, matching REF bases, and available DP, GQ and AD fields. These checks establish technical consistency, not causality or phase.

My validator also checks chromosome names, allele syntax, positive positions, complete pairs, duplicate hypotheses, finite EPCR and exact native-model membership. The repository includes **11 synthetic tests**, covering malformed inputs, duplicate/reversed pairs, missing scores and ordering invariance. Those tests measure software behavior rather than clinical accuracy.

My repository includes the code, configuration, report and CSV, along with file checksums and validation receipts. Authorized users can rerun the analysis with their own gated inputs or reproduce just the review/export from the saved native JSONL. Packaging did not require a new patient run; I checked the portable full-analysis wrapper in preparation mode rather than running it end-to-end again.

# What still needs confirmation

The most informative next evidence would be parental segregation or another validated phasing method, followed by functional assessment of p.Asn1002Lys. If the alleles are in cis, or the missense allele has no relevant effect, the proposed recessive explanation needs reconsideration.

My search was coding/splice-oriented. It did not comprehensively evaluate regulatory variants, SV/CNV, mosaicism, chromosome-scale changes or raw reads. I retained source-native allele representations; differences in reference/decoy coverage limit broader normalization claims. The source index is older than the VCF modification time, although the exact submitted-allele lookups passed.

Finally, this was a single-case analysis with retrospective manual review, not a blinded cohort benchmark. I have not measured general diagnostic accuracy or an official challenge score.

# AI assistance

I used OpenAI's ChatGPT Plus through OpenCode for code development and debugging, workflow review, and drafting and editing this report. Exomiser performed variant annotation and prioritization locally; the final ranking also includes the case-specific review described above. My ChatGPT “Improve the model for everyone” setting was off.

# Acknowledgement

This work was made possible through the Hackathon, organized by Sage Bionetworks in partnership with the MVA Society, Hugging Face, and BEACON (The Benchmarking, Evaluation, and Assessment Consortium for Science), with prize sponsorship from AWS and Anthropic. We are deeply grateful to the child and their family who generously contributed their data and their story to advance research into this rare disease. We acknowledge their trust in making this Hackathon possible.

# References

1. Sage Bionetworks. *MVA Hackathon 2026 Data* (2026). [Official gated dataset](https://huggingface.co/datasets/SageBio/mva-hackathon-2026-data).
2. Sage Bionetworks. *Rare Disease, Real Kid: MVA Hackathon 2026*. [Track 1 instructions and official rules](https://huggingface.co/spaces/SageBio/rare-disease-real-kid-mva-hackathon-2026).
3. Exomiser developers. *Exomiser 15.1.0*. [Software release](https://github.com/exomiser/Exomiser/releases/tag/15.1.0) and [documentation](https://exomiser.readthedocs.io/).
4. NCBI ClinVar. [Variation 533901, BUB1B](https://www.ncbi.nlm.nih.gov/clinvar/variation/533901/). Interpretation in my run used the recorded release 2602 resources, not an assumed current live assertion.
5. Hanks S, et al. Constitutional aneuploidy and cancer predisposition caused by biallelic mutations in BUB1B. *Nature Genetics* (2004), 36:1159–1161. [doi:10.1038/ng1449](https://doi.org/10.1038/ng1449).

# Reproduction identifiers

Input VCF SHA-256:

`bec64c68d3ad10d05b8071d07cdf87d217013d66d3ba02e24b505035c9d42175`

Native JSONL SHA-256:

`85b2f11b5150a73d294e4ce3748b4c3c7a62f9346b12e9cb5eb77cb3480c8697`
