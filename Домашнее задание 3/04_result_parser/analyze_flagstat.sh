#!/bin/bash

# === Входные данные ===
INPUT="working_files/flagstat.txt"
OUTPUT="working_files/mapping_quality.txt"

# === Проверка наличия входного файла ===
if [[ ! -f "$INPUT" ]]; then
    echo "Error: $INPUT not found!" >&2
    exit 1
elif [[ ! -s "$INPUT" ]]; then
    echo "Error: $INPUT is empty!" >&2
    exit 1
fi

# === Извлечение чисел ===
total=$(grep "in total" "$INPUT" | awk '{print $1}')
mapped=$(grep "mapped (" "$INPUT" | awk '{print $1}')

if [[ -z "$total" || -z "$mapped" ]]; then
    echo "Error: Could not extract read counts from $INPUT" >&2
    exit 1
fi

if (( total == 0 )); then
    echo "Error: Total reads is 0 - division by zero" >&2
    exit 1
fi

percent=$(awk -v mapped="$mapped" -v total="$total" 'BEGIN {printf "%.2f", (mapped/total)*100}')

# === Вывод результата ===

{
    echo "Mapped reads: $mapped / $total (${percent}%)"
    
    # === Decision branching ===
    if (( $(echo "$percent > 90" | bc -l) )); then
        echo "Mapping quality: OK"
    else
        echo "Mapping quality: NOT OK"
    fi
} | tee "$OUTPUT"

exit 0
