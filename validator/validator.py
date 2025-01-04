import subprocess
import logging
import os

class Validator:
    def __init__(self, target_file: str, llvm_cov_path: str = 'llvm-cov', coverage_threshold: float = 80.0,
                 output_dir: str = './outputs', log_file: str = 'validation_log.txt'):
        self.target_file = target_file
        self.llvm_cov_path = llvm_cov_path
        self.coverage_threshold = coverage_threshold  # 设置覆盖率阈值
        self.output_dir = output_dir
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)

        # 配置日志输出到文件
        logging.basicConfig(level=logging.INFO, filename=self.log_file, filemode='w',
                            format='%(asctime)s - %(levelname)s - %(message)s')

        # 创建输出目录结构
        self.temp_dir = os.path.join(self.output_dir, 'temp')
        self.coverage_dir = os.path.join(self.temp_dir, 'coverage')
        self.error_log_dir = os.path.join(self.temp_dir, 'error_log')
        self.validated_fuzz_drivers_dir = os.path.join(self.output_dir, 'validated_fuzz_drivers')

        os.makedirs(self.coverage_dir, exist_ok=True)
        os.makedirs(self.error_log_dir, exist_ok=True)
        os.makedirs(self.validated_fuzz_drivers_dir, exist_ok=True)

    def compile_with_coverage(self, fuzz_driver_file: str) -> str | None:
        """
        Compile fuzz driver and target file with coverage instrumentation.
        """
        try:
            # 编译命令
            compile_command = [
                'clang', '-g', '-fsanitize=fuzzer', '-fsanitize=address', '-std=c11',
                '-fprofile-instr-generate', '-fcoverage-mapping', '-o', 'fuzz_driver',
                fuzz_driver_file, self.target_file, '-I/usr/include/libxml2',
                '-L/usr/lib/x86_64-linux-gnu', '-lxml2'
            ]

            # 执行编译
            subprocess.run(compile_command, check=True)
            self.logger.info("Fuzz driver compiled with coverage.")

            return fuzz_driver_file

        except subprocess.CalledProcessError as e:
            # 编译失败，保存错误信息到文件
            error_log_path = os.path.join(self.error_log_dir, 'raw_error_log.txt')
            self.logger.error(f"Compilation failed: {e}")
            with open(error_log_path, "w") as error_file:
                error_file.write(f"Compilation failed with error: {str(e)}\n")
            return None

    def run_fuzzing_and_measure_coverage(self) -> float:
        """
        Run fuzz testing and measure code coverage.
        """
        try:
            # 运行 fuzz 驱动
            run_command = ['./fuzz_driver']
            subprocess.run(run_command, check=True)
            self.logger.info("Fuzz driver executed.")

            # 生成覆盖率数据
            llvm_cov_command = [
                self.llvm_cov_path, 'gcov', 'fuzz_driver.profraw'
            ]
            subprocess.run(llvm_cov_command, check=True)

            # 获取覆盖率报告
            coverage_command = [
                'llvm-cov', 'report', './fuzz_driver', '-instr-profile=default.profdata'
            ]
            result = subprocess.run(coverage_command, capture_output=True, text=True)
            self.logger.info("Coverage report generated.")

            # 保存覆盖率报告到文件
            coverage_file_path = os.path.join(self.coverage_dir, 'raw_coverage.txt')
            with open(coverage_file_path, "w") as coverage_file:
                coverage_file.write(result.stdout)

            # 解析报告以提取覆盖率百分比
            coverage_line = None
            for line in result.stdout.splitlines():
                if "Total" in line:
                    coverage_line = line
                    break

            if coverage_line:
                coverage_percentage = float(coverage_line.split()[3].replace('%', ''))
                self.logger.info(f"Code coverage: {coverage_percentage}%")
                return coverage_percentage
            else:
                self.logger.error("Coverage data not found in the report.")
                return 0.0

        except Exception as e:
            self.logger.error(f"Error during fuzzing and coverage measurement: {str(e)}")
            return 0.0

    def validate_fuzzing(self, driver_file: str) -> float:
        """
        Full validation process: compile, run fuzzing, and measure coverage.
        """
        try:
            # 编译 fuzz 驱动
            compiled_driver = self.compile_with_coverage(driver_file)

            # 运行 fuzzing 并测量覆盖率
            coverage_percentage = self.run_fuzzing_and_measure_coverage()

            # 如果覆盖率低于阈值，则保存详细覆盖率信息到文件
            if coverage_percentage < self.coverage_threshold:
                coverage_report_path = os.path.join(self.coverage_dir, 'coverage_report.txt')
                with open(coverage_report_path, "w") as report_file:
                    report_file.write(f"Coverage percentage: {coverage_percentage}%\n")
                    report_file.write("Coverage report:\n")
                    report_file.write(f"Details of {compiled_driver}:\n")
                    report_file.write(str(compiled_driver))

            # 如果覆盖率合格，保存验证过的 fuzz 驱动到 validated_fuzz_drivers 文件夹
            if coverage_percentage >= self.coverage_threshold:
                validated_driver_path = os.path.join(self.validated_fuzz_drivers_dir, 'validated_fuzz_driver.c')
                with open(validated_driver_path, "w") as validated_file:
                    with open(compiled_driver, "r") as driver:
                        validated_file.write(driver.read())

            return coverage_percentage

        except Exception as e:
            self.logger.error(f"Error during fuzzing validation: {str(e)}")
            return 0.0


# 提供可供外部调用的接口函数
def validate_fuzzing_for_target(driver_file: str, target_file: str, llvm_cov_path: str = 'llvm-cov',
                                coverage_threshold: float = 80.0, output_dir: str = './outputs',
                                log_file: str = 'validation_log.txt') -> float:
    """
    Interface function for validating fuzzing and coverage for a given driver file and target file.
    :param driver_file: Fuzz driver source code file path
    :param target_file: Target file to be fuzzed
    :param llvm_cov_path: Path to llvm-cov binary (default: 'llvm-cov')
    :param coverage_threshold: Minimum acceptable coverage percentage (default: 80.0)
    :param output_dir: Directory to store outputs (default: './outputs')
    :param log_file: Log file to record logs (default: 'validation_log.txt')
    :return: Coverage percentage achieved after fuzzing
    """
    validator = Validator(target_file, llvm_cov_path, coverage_threshold, output_dir, log_file)
    return validator.validate_fuzzing(driver_file)


# 示例：如何在其他程序中调用接口
if __name__ == "__main__":
    # 假设 driver_file 和 target_file 传入
    driver_file = ""  # 替换为你的 fuzz driver 文件路径
    target_file = ""  # 替换为你的目标文件路径

    # 调用接口进行 fuzz 验证
    coverage = validate_fuzzing_for_target(driver_file, target_file)

    if coverage > 0:
        print(f"Fuzzing completed with {coverage}% code coverage.")
    else:
        print("Fuzzing failed to produce meaningful coverage.")