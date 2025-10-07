#!/bin/bash

echo "Fetching all repositories..."

# 親リポジトリ
echo "Fetching docker_miniconda..."
git fetch

# 各サブリポジトリ
for repo in CompresionRain FrontLine PressurePattern WeatherLLM TyphoonForecast AWCGS; do
    if [ -d "src/$repo/.git" ]; then
        echo "Fetching $repo..."
        cd "src/$repo"
        git fetch
        cd ../..
    fi
done

echo "Done!"