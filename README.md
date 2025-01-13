# llm-fuzz-driver
**A LLM based fuzz-driver generation tool.** We use the LLM model to generate the code for the target driver and 
then implemented a validator and refinement process to ensure the generated code is correct and efficient.

The project is developed as a part of the course project for the course "Software Testing" at **Nanjing University**. 
The whole project is under **MIT License**.

## Overall Structure

![structure](./structure.png)

## How to Run

Set the configuration in `config.json` file. An example configuration file (for `libxml2/xmllint`) is as follows:

```json
{
    "project_name": "libxml2",
    "target_name": "xmllint",
    "target_function": "main",
    "target_file": "./targets/libxml2-2.13.4/xmllint.c",
    "test_driver_model_code_path": "./prompt_generator/model.c",
    "max_iterations": 10,
    "compile_command": [
        "clang",
        "-g",
        "-fsanitize=fuzzer",
        "-fsanitize=address",
        "-std=c11",
        "-fprofile-instr-generate",
        "-fcoverage-mapping",
        "-o",
        "fuzz_driver",
        "xmllint_fuzz_driver.c",
        "-I./include",
        "./.libs/libxml2.a"
    ]
}

```

The meaning of each field is as follows:

| Field                         | Description                                                        |
|-------------------------------|--------------------------------------------------------------------|
| `project_name`                | The name of the project                                            |
| `target_name`                 | The name of the target                                             |
| `target_function`             | The name of the target function                                    |
| `target_file`                 | The path to the target file (after prebuild)                       |
| `test_driver_model_code_path` | The path to the model code (default: `./prompt_generator/model.c`) |
| `max_iterations`              | The maximum number of iterations                                   |
| `compile_command`             | The compile command                                                |


Then, prepare a prebuild shell script that builds the target and generates the prebuild files. An example prebuild 
shell 
script (for `libxml2/xmllint`) is as follows:

```bash
tar -zxvf libxml2-2.13.4.tar.gz
cd libxml2-2.13.4
./autogen.sh
./configure --disable-shared
make
echo 'libxml2 build done'
```

After you set up, run the tool with the following command:

```bash
python3 main.py <config_file_path> <prebuild_shell_path>
```

### Examples

We provide three examples of configuration files and prebuild shell scripts along with the target files in the 
`targets` directory. Here is the list of the examples:

| Project & Target  | Configuration File              | Prebuild Shell Script           |
|-------------------|---------------------------------|---------------------------------|
| `libxml2/xmllint` | `./targets/libxml2_config.json` | `./targets/libxml2_prebuild.sh` |
| `libjpeg/djpeg`   | `./targets/libjpeg_config.json` | `./targets/libjpeg_prebuild.sh` |
| `libpng/readpng`  | `./targets/libpng_config.json`  | `./targets/libpng_prebuild.sh`  |

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
        │   └── raw.c
        ├── coverage
        │   └── raw_coverage.txt
        └── error_log
            └── raw_error_log.txt
```
## Demonstration Video
[link](https://www.bilibili.com/video/BV1FaruYMEJy/?vd_source=15a16af321809f158275c13088f407a6)
