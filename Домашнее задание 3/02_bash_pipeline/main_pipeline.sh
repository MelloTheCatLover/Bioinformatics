
#!/bin/bash

# === Конфигурация ===
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

INPUT_DIR="input"
WORK_DIR="working_files"
FINAL_DIR="output"
SCRIPTS_DIR="scripts"

if [[ "$(basename "$SCRIPT_DIR")" == "scripts" ]]; then
    INPUT_DIR="../input"
    WORK_DIR="../working_files"
    FINAL_DIR="../output"
    SCRIPTS_DIR="."
fi

READ1="${INPUT_DIR}/SRR2584863_1.fastq"
READ2="${INPUT_DIR}/SRR2584863_2.fastq"
REFERENCE="${INPUT_DIR}/ecoli.fa"
REFERENCE_COPY="${WORK_DIR}/ecoli.fa"
BWA_INDEX_PREFIX="${WORK_DIR}/ecoli"
SAMPLE="sample"
THREADS=4

# === Флаги ===
CLEAN_WORKING=false  # Удалять временные файлы после завершения
SKIP_VARIANTS=false  # Пропустить вызов вариантов

# Разбор аргументов командной строки
for arg in "$@"; do
    case $arg in
        --clean)
            CLEAN_WORKING=true
            ;;
        --no-variants)
            SKIP_VARIANTS=true
            ;;
        *)
            echo -e "\n=======================ERROR======================="
            echo " Unknown option: $arg"
            echo " Usage: $0 [--clean] [--no-variants]"
            echo "==================================================="
            exit 1
            ;;
    esac
done

# === Проверка входных файлов и директорий ===
echo -e "\n=============================================="
echo " INPUT VERIFICATION"
echo "=============================================="

if [[ ! -d "$INPUT_DIR" ]]; then
    echo -e "\n=======================ERROR======================="
    echo " Input directory $INPUT_DIR not found!"
    echo " Текущая директория: $(pwd)"
    echo " Запустите скрипт из корневой директории проекта"
    echo "==================================================="
    exit 1
fi

# Проверка наличия необходимых файлов
missing_files=()
for file in "$READ1" "$READ2" "$REFERENCE"; do
    if [[ ! -f "$file" ]]; then
        missing_files+=("$file")
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    echo -e "\n=======================ERROR======================="
    echo " Missing required input files:"
    for file in "${missing_files[@]}"; do
        echo " - $file"
    done
    echo "==================================================="
    exit 1
fi

# Создание рабочих директорий
mkdir -p "$WORK_DIR" "$FINAL_DIR" "${WORK_DIR}/qc_reports"

# === 1. FastQC - контроль качества ===
echo -e "\n=============================================="
echo " FASTQC QUALITY CONTROL"
echo "=============================================="
if ! command -v fastqc &> /dev/null; then
    echo -e "\n=======================ERROR======================="
    echo " fastqc not found in PATH"
    echo " Please install FastQC and add to PATH"
    echo "==================================================="
    exit 1
fi
fastqc "$READ1" "$READ2" -o "${WORK_DIR}/qc_reports/"

# === 2. Индексация и выравнивание ===
echo -e "\n=============================================="
echo " INDEX & ALIGNMENT"
echo "=============================================="

echo -e "\n> Copying reference genome..."
cp "$REFERENCE" "$REFERENCE_COPY"

echo -e "\n> Indexing reference genome..."
if ! command -v bwa &> /dev/null; then
    echo -e "\n=======================ERROR======================="
    echo " bwa not found in PATH"
    echo " Please install BWA and add to PATH"
    echo "==================================================="
    exit 1
fi
bwa index -p "$BWA_INDEX_PREFIX" "$REFERENCE_COPY"

echo -e "\n> Running BWA alignment..."
bwa mem -t "$THREADS" "$BWA_INDEX_PREFIX" "$READ1" "$READ2" > "${WORK_DIR}/${SAMPLE}.sam"

# === 3. Конвертация SAM в BAM ===
echo -e "\n=============================================="
echo " SAM TO BAM CONVERSION"
echo "=============================================="
if ! command -v samtools &> /dev/null; then
    echo -e "\n=======================ERROR======================="
    echo " samtools not found in PATH"
    echo " Please install Samtools and add to PATH"
    echo "==================================================="
    exit 1
fi
samtools view -@ "$THREADS" -Sb "${WORK_DIR}/${SAMPLE}.sam" > "${WORK_DIR}/${SAMPLE}.bam"

# === 4. Статистика картирования ===
echo -e "\n=============================================="
echo " MAPPING STATISTICS"
echo "=============================================="
echo -e "\n> Running samtools flagstat..."
samtools flagstat "${WORK_DIR}/${SAMPLE}.bam" > "${WORK_DIR}/flagstat.txt"

# === 5. Анализ статистики картирования ===
echo -e "\n=============================================="
echo " MAPPING QUALITY ANALYSIS"
echo "=============================================="
if [[ -f "${SCRIPTS_DIR}/analyze_flagstat.sh" ]]; then
    bash "${SCRIPTS_DIR}/analyze_flagstat.sh" "${WORK_DIR}/flagstat.txt" > "${WORK_DIR}/mapping_quality.txt"
else
    echo -e "\n> WARNING: analyze_flagstat.sh script not found"
    echo "> Creating default mapping_quality.txt..."
    echo "OK" > "${WORK_DIR}/mapping_quality.txt"
fi

# === 6. Сортировка и индексация BAM ===
echo -e "\n=============================================="
echo " BAM SORTING AND INDEXING"
echo "=============================================="
if grep -q "OK" "${WORK_DIR}/mapping_quality.txt"; then
    echo -e "\n> Mapping quality OK"
    echo "> Sorting BAM file..."
    samtools sort -@ "$THREADS" -o "${FINAL_DIR}/${SAMPLE}.sorted.bam" "${WORK_DIR}/${SAMPLE}.bam"

    echo -e "\n> Индексация отсортированного BAM..."
    samtools index "${FINAL_DIR}/${SAMPLE}.sorted.bam"
else
    echo -e "\n=============================================="
    echo " Mapping quality too low"
    echo " Skipping sorting and variant calling"
    echo "=============================================="
    [[ "$CLEAN_WORKING" == true ]] && rm -rf "$WORK_DIR"
    exit 0
fi

# === 7. Вызов вариантов ===
if [[ "$SKIP_VARIANTS" == false ]]; then
    echo -e "\n=============================================="
    echo " Running freebayes..."
    echo "=============================================="
    if ! command -v freebayes &> /dev/null; then
        echo -e "\n=======================ERROR======================="
        echo " freebayes not found in PATH."
        echo " Please install freebayes and add to PATH"
        echo "==================================================="
        exit 1
    fi
    freebayes -f "$REFERENCE_COPY" "${FINAL_DIR}/${SAMPLE}.sorted.bam" > "${FINAL_DIR}/${SAMPLE}.vcf"
else
    echo -e "\n=============================================="
    echo " SKIPPING VARIAN CALLING (--no-variants flag used)."
    echo "=============================================="
fi

# === 8. Очистка временных файлов ===
if [[ "$CLEAN_WORKING" == true ]]; then
    echo -e "\n=============================================="
    echo " CLEANING UP WORKING DERICTORY"
    echo "=============================================="
    echo -e "\n> Deleting working directory"
    rm -rf "$WORK_DIR"
fi

echo -e "\n=============================================="
echo " PIPELINE FINISHED SUCCESSFULLY!"
echo " Results are in: $FINAL_DIR"
echo "=============================================="
