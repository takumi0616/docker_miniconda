#!/bin/bash

echo "Cycling through all project files..."

# プロジェクトディレクトリのリスト
projects=(
    "AWCGS"
    "CompresionRain"
    "FrontLine"
    "PressurePattern"
    "TyphoonForecast"
    "WeatherLLM"
    "3D_avatars"
)

# 各プロジェクトの主要ファイルを開く
for project in "${projects[@]}"; do
    echo "=== Processing $project ==="
    
    # README.mdを開く
    if [ -f "src/$project/README.md" ]; then
        code "src/$project/README.md"
        sleep 2
    fi
    
    # .pyファイルを1つ開く（Gitの認識を促す）
    py_file=$(find "src/$project" -name "*.py" -type f | head -1)
    if [ -n "$py_file" ]; then
        code "$py_file"
        sleep 1
    fi
done

# 最後にすべてのREADMEを一括で開く
echo "Opening all README files together..."
code src/*/README.md