# llm-fuzz-driver
A LLM based fuzz-driver generation tool.

## Overall Structure

![structure](./structure.png)

## Output Directory Structure

The `outputs` directory is where the generated files are stored. The whole directory is automatically created by the 
tool **on runtime**. The directory structure is as follows:

```
./outputs
    ├── validated_fuzz_drivers
    │   ├── validated_fuzz_driver_1.c
    │   ├── validated_fuzz_driver_2.c
    │   └── ...
    └── temp
        ├── candidate_fuzz_drivers
        │   ├── raw.c
        │   ├── mutant_1.c
        │   ├── mutant_2.c
        │   └── ...
        ├── coverage
        │   ├── raw_coverage.txt
        │   ├── mutant_1_coverage.txt
        │   ├── mutant_2_coverage.txt
        │   └── ...
        └── error_log
            ├── raw_error_log.txt
            ├── mutant_1_error_log.txt
            ├── mutant_2_error_log.txt
            └── ...
```