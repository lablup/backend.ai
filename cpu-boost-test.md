# CPU Boost Feature Testing Guide

## Overview

이 문서는 Backend.AI의 CPU boost 기능 테스트를 위한 가이드입니다. CPU boost는 컨테이너 초기 로딩 시 일시적으로 더 많은 CPU를 할당하여 시작 시간을 단축하는 기능입니다.

**핵심 질문:**
- CPU boost가 실제로 container loading time을 얼마나 단축시키는가?
- 어떤 종류의 workload에서 효과가 큰가?
- Side effect는 무엇인가? (다른 컨테이너 영향, 리소스 경합 등)

---

## Test Cases Summary

| # | Category | Image | Expected Improvement | Priority |
|---|----------|-------|---------------------|----------|
| 1 | Deep Learning | `pytorch/pytorch:latest` | 30-50% | 🔥 High |
| 2 | Deep Learning | `tensorflow/tensorflow:latest` | 30-50% | 🔥 High |
| 3 | JIT Runtime | `openjdk:11` | 20-40% | ⚡ High |
| 4 | JIT Runtime | `julia:latest` | 20-40% | ⚡ High |
| 5 | Data Science | `jupyter/scipy-notebook:latest` | 15-25% | 📊 Medium |
| 6 | Node.js | `node:18` (with heavy packages) | 10-20% | 📦 Medium |
| 7 | Baseline | `python:3.11-slim` | <5% | 📏 Control |
| 8 | Backend.AI | `lablup/python-pytorch:2.0-py311` | 25-45% | 🎯 Real-world |
| 9 | Backend.AI | `lablup/python-tensorflow:2.13-py311` | 25-45% | 🎯 Real-world |
| 10 | Backend.AI | `lablup/ngc-tensorflow:23.08-tf2-py3` | 30-50% | 🎯 Real-world |

---

## Test Case Details

### 1. Deep Learning - PyTorch

**Image:** `pytorch/pytorch:latest`

**Why Test:** PyTorch initialization involves loading heavy C++ extensions, CUDA libraries, and performing JIT compilation.

**Test Script:** `tests/pytorch_load_test.py`
```python
#!/usr/bin/env python3
import time
import json
import os

metrics = {
    "test_name": "pytorch_load",
    "cpu_allocated": os.cpu_count(),
    "container_start_time": time.time(),
}

# Phase 1: Import time (가장 CPU intensive)
print("=== Phase 1: Import ===")
start = time.time()
import torch
import torchvision
import torchaudio
metrics["import_time"] = time.time() - start
print(f"Import completed in {metrics['import_time']:.2f}s")

# Phase 2: First computation (GPU/CPU initialization)
print("\n=== Phase 2: First Computation ===")
start = time.time()
x = torch.randn(2000, 2000)
y = torch.matmul(x, x)
z = torch.sum(y)
metrics["first_computation_time"] = time.time() - start
print(f"First computation: {metrics['first_computation_time']:.2f}s")

# Phase 3: Second computation (warmed up)
print("\n=== Phase 3: Second Computation ===")
start = time.time()
x2 = torch.randn(2000, 2000)
y2 = torch.matmul(x2, x2)
z2 = torch.sum(y2)
metrics["second_computation_time"] = time.time() - start
print(f"Second computation: {metrics['second_computation_time']:.2f}s")

metrics["total_time"] = time.time() - metrics["container_start_time"]

print(f"\n=== METRICS_JSON ===")
print(json.dumps(metrics, indent=2))
```

**Expected Results:**
- **Baseline (no boost):** Import ~8-12s, First computation ~2-3s
- **With 2x boost:** Import ~4-6s, First computation ~1-2s
- **Improvement:** 30-50% reduction in total initialization time

---

### 2. Deep Learning - TensorFlow

**Image:** `tensorflow/tensorflow:latest`

**Why Test:** TensorFlow has extensive lazy initialization and CUDA runtime loading.

**Test Script:** `tests/tensorflow_load_test.py`
```python
#!/usr/bin/env python3
import time
import json
import os

metrics = {
    "test_name": "tensorflow_load",
    "cpu_allocated": os.cpu_count(),
    "container_start_time": time.time(),
}

# Phase 1: Import
print("=== Phase 1: Import ===")
start = time.time()
import tensorflow as tf
metrics["import_time"] = time.time() - start
print(f"Import completed in {metrics['import_time']:.2f}s")

# Phase 2: Graph building
print("\n=== Phase 2: Graph Building ===")
start = time.time()
x = tf.constant([[1.0, 2.0], [3.0, 4.0]])
y = tf.constant([[1.0], [2.0]])
result = tf.matmul(x, y)
metrics["graph_build_time"] = time.time() - start
print(f"Graph build: {metrics['graph_build_time']:.2f}s")

# Phase 3: First execution
print("\n=== Phase 3: First Execution ===")
start = time.time()
with tf.device('/CPU:0'):
    a = tf.random.normal([2000, 2000])
    b = tf.matmul(a, a)
    c = tf.reduce_sum(b)
metrics["first_execution_time"] = time.time() - start
print(f"First execution: {metrics['first_execution_time']:.2f}s")

metrics["total_time"] = time.time() - metrics["container_start_time"]

print(f"\n=== METRICS_JSON ===")
print(json.dumps(metrics, indent=2))
```

**Expected Results:**
- **Baseline:** Import ~10-15s, Graph build ~1-2s, First execution ~2-3s
- **With 2x boost:** Import ~5-8s, Graph build ~0.5-1s, First execution ~1-1.5s
- **Improvement:** 35-50% reduction

---

### 3. JIT Runtime - Java (OpenJDK)

**Image:** `openjdk:11`

**Why Test:** JVM initialization and class loading is CPU-intensive, especially with JIT compilation.

**Test Script:** `tests/java_load_test/LoadTest.java`
```java
import java.util.*;
import java.util.concurrent.*;

public class LoadTest {
    public static void main(String[] args) {
        long containerStart = System.currentTimeMillis();
        Map<String, Object> metrics = new HashMap<>();

        metrics.put("test_name", "java_load");
        metrics.put("cpu_allocated", Runtime.getRuntime().availableProcessors());
        metrics.put("container_start_time", containerStart);

        // Phase 1: Class loading and JVM initialization
        System.out.println("=== Phase 1: Class Loading ===");
        long start = System.currentTimeMillis();
        List<String> list = new ArrayList<>();
        for (int i = 0; i < 100000; i++) {
            list.add("String" + i);
        }
        Collections.sort(list);
        metrics.put("class_loading_time", System.currentTimeMillis() - start);
        System.out.println("Class loading: " + metrics.get("class_loading_time") + "ms");

        // Phase 2: First computation (JIT compilation)
        System.out.println("\n=== Phase 2: First Computation ===");
        start = System.currentTimeMillis();
        double result = 0;
        for (int i = 0; i < 10000000; i++) {
            result += Math.sqrt(i) * Math.sin(i);
        }
        metrics.put("first_computation_time", System.currentTimeMillis() - start);
        System.out.println("First computation: " + metrics.get("first_computation_time") + "ms");

        // Phase 3: Second computation (JIT optimized)
        System.out.println("\n=== Phase 3: Second Computation ===");
        start = System.currentTimeMillis();
        result = 0;
        for (int i = 0; i < 10000000; i++) {
            result += Math.sqrt(i) * Math.sin(i);
        }
        metrics.put("second_computation_time", System.currentTimeMillis() - start);
        System.out.println("Second computation: " + metrics.get("second_computation_time") + "ms");

        metrics.put("total_time", System.currentTimeMillis() - containerStart);

        System.out.println("\n=== METRICS_JSON ===");
        System.out.println(new com.google.gson.Gson().toJson(metrics));
    }
}
```

**Expected Results:**
- **Baseline:** Class loading ~1-2s, First computation ~3-5s
- **With 2x boost:** Class loading ~0.5-1s, First computation ~1.5-2.5s
- **Improvement:** 25-40% reduction

---

### 4. JIT Runtime - Julia

**Image:** `julia:latest`

**Why Test:** Julia's first execution includes JIT compilation, making it extremely CPU-intensive.

**Test Script:** `tests/julia_load_test.jl`
```julia
using JSON
using LinearAlgebra
using Statistics

metrics = Dict(
    "test_name" => "julia_load",
    "cpu_allocated" => Sys.CPU_THREADS,
    "container_start_time" => time(),
)

# Phase 1: Package precompilation
println("=== Phase 1: Package Loading ===")
start = time()
using DataFrames, Plots
metrics["package_load_time"] = time() - start
println("Package loading: $(metrics["package_load_time"])s")

# Phase 2: First computation (JIT compilation)
println("\n=== Phase 2: First Computation (JIT) ===")
start = time()
A = rand(1000, 1000)
B = A * A
C = eigvals(B)
metrics["first_computation_time"] = time() - start
println("First computation: $(metrics["first_computation_time"])s")

# Phase 3: Second computation (compiled)
println("\n=== Phase 3: Second Computation (Compiled) ===")
start = time()
A2 = rand(1000, 1000)
B2 = A2 * A2
C2 = eigvals(B2)
metrics["second_computation_time"] = time() - start
println("Second computation: $(metrics["second_computation_time"])s")

metrics["total_time"] = time() - metrics["container_start_time"]

println("\n=== METRICS_JSON ===")
println(JSON.json(metrics, 2))
```

**Expected Results:**
- **Baseline:** Package load ~15-20s, First computation ~5-8s, Second ~0.5-1s
- **With 2x boost:** Package load ~8-10s, First computation ~2-4s, Second ~0.5-1s
- **Improvement:** 35-45% reduction

---

### 5. Data Science Stack - Python Scientific

**Image:** `jupyter/scipy-notebook:latest`

**Why Test:** Multiple C extensions (NumPy, SciPy, Pandas) loading simultaneously.

**Test Script:** `tests/scipy_load_test.py`
```python
#!/usr/bin/env python3
import time
import json
import os

metrics = {
    "test_name": "scipy_load",
    "cpu_allocated": os.cpu_count(),
    "container_start_time": time.time(),
}

# Phase 1: Import scientific stack
print("=== Phase 1: Scientific Stack Import ===")
start = time.time()
import numpy as np
import pandas as pd
import scipy
import scipy.stats
import matplotlib.pyplot as plt
import sklearn
from sklearn.ensemble import RandomForestClassifier
metrics["import_time"] = time.time() - start
print(f"Import completed in {metrics['import_time']:.2f}s")

# Phase 2: First data processing
print("\n=== Phase 2: First Data Processing ===")
start = time.time()
df = pd.DataFrame(np.random.randn(100000, 50))
result = df.describe()
corr_matrix = df.corr()
metrics["first_processing_time"] = time.time() - start
print(f"First processing: {metrics['first_processing_time']:.2f}s")

# Phase 3: ML model training
print("\n=== Phase 3: ML Model Training ===")
start = time.time()
X = np.random.randn(10000, 20)
y = np.random.randint(0, 2, 10000)
clf = RandomForestClassifier(n_estimators=100, n_jobs=-1)
clf.fit(X, y)
metrics["ml_training_time"] = time.time() - start
print(f"ML training: {metrics['ml_training_time']:.2f}s")

metrics["total_time"] = time.time() - metrics["container_start_time"]

print(f"\n=== METRICS_JSON ===")
print(json.dumps(metrics, indent=2))
```

**Expected Results:**
- **Baseline:** Import ~5-8s, First processing ~2-3s, ML training ~3-5s
- **With 2x boost:** Import ~3-4s, First processing ~1-2s, ML training ~2-3s
- **Improvement:** 20-30% reduction

---

### 6. Node.js with Heavy Packages

**Image:** `node:18`

**Test Script:** `tests/nodejs_load_test/package.json`
```json
{
  "name": "nodejs-load-test",
  "version": "1.0.0",
  "dependencies": {
    "webpack": "^5.88.0",
    "@babel/core": "^7.22.0",
    "typescript": "^5.1.0",
    "react": "^18.2.0",
    "lodash": "^4.17.21"
  }
}
```

**Test Script:** `tests/nodejs_load_test/test.js`
```javascript
const { performance } = require('perf_hooks');
const os = require('os');

const metrics = {
    test_name: 'nodejs_load',
    cpu_allocated: os.cpus().length,
    container_start_time: performance.now(),
};

// Phase 1: Module loading
console.log('=== Phase 1: Module Loading ===');
const start1 = performance.now();
const webpack = require('webpack');
const babel = require('@babel/core');
const typescript = require('typescript');
const React = require('react');
const _ = require('lodash');
metrics.import_time = (performance.now() - start1) / 1000;
console.log(`Import completed in ${metrics.import_time.toFixed(2)}s`);

// Phase 2: First processing
console.log('\n=== Phase 2: First Processing ===');
const start2 = performance.now();
const data = _.range(1000000);
const result = _.map(data, n => n * 2);
const sum = _.sum(result);
metrics.first_processing_time = (performance.now() - start2) / 1000;
console.log(`First processing: ${metrics.first_processing_time.toFixed(2)}s`);

metrics.total_time = (performance.now() - metrics.container_start_time) / 1000;

console.log('\n=== METRICS_JSON ===');
console.log(JSON.stringify(metrics, null, 2));
```

**Expected Results:**
- **Baseline:** Import ~3-5s, First processing ~1-2s
- **With 2x boost:** Import ~2-3s, First processing ~0.5-1s
- **Improvement:** 15-25% reduction

---

### 7. Baseline - Lightweight Python

**Image:** `python:3.11-slim`

**Why Test:** Control group to measure CPU boost overhead.

**Test Script:** `tests/baseline_test.py`
```python
#!/usr/bin/env python3
import time
import json
import os

metrics = {
    "test_name": "baseline",
    "cpu_allocated": os.cpu_count(),
    "container_start_time": time.time(),
}

# Phase 1: Minimal imports
print("=== Phase 1: Import ===")
start = time.time()
import sys
import math
metrics["import_time"] = time.time() - start
print(f"Import completed in {metrics['import_time']:.4f}s")

# Phase 2: Simple computation
print("\n=== Phase 2: Simple Computation ===")
start = time.time()
result = sum(i**2 for i in range(10000))
metrics["computation_time"] = time.time() - start
print(f"Computation: {metrics['computation_time']:.4f}s")

metrics["total_time"] = time.time() - metrics["container_start_time"]

print(f"\n=== METRICS_JSON ===")
print(json.dumps(metrics, indent=2))
```

**Expected Results:**
- **Baseline:** Total ~0.1-0.2s
- **With 2x boost:** Total ~0.1-0.2s
- **Improvement:** <5% (overhead measurement)

---

### 8-10. Backend.AI Real-world Images

**Images:**
- `lablup/python-pytorch:2.0-py311`
- `lablup/python-tensorflow:2.13-py311`
- `lablup/ngc-tensorflow:23.08-tf2-py3`

**Test Script:** Same as PyTorch/TensorFlow tests above

**Expected Results:**
- Similar to upstream PyTorch/TensorFlow but may include additional Backend.AI specific initialization
- **Improvement:** 25-50% depending on image optimization level

---

## Test Methodology

### Configuration Matrix

Test each image with the following configurations:

| Config ID | cpu-boost-enabled | cpu-boost-factor | cpu-boost-duration | Purpose |
|-----------|-------------------|------------------|-------------------|---------|
| `baseline` | `false` | - | - | Baseline performance |
| `boost-1.5x` | `true` | `1.5` | `30` | Conservative boost |
| `boost-2x` | `true` | `2.0` | `60` | Standard boost |
| `boost-3x` | `true` | `3.0` | `60` | Aggressive boost |
| `boost-5x` | `true` | `5.0` | `120` | Maximum boost |

### Metrics to Collect

For each test run, collect:

1. **Timing Metrics:**
   - `import_time`: Library/package import duration
   - `first_computation_time`: First computation (cold start)
   - `second_computation_time`: Second computation (warm start)
   - `total_time`: Container start to test completion

2. **Resource Metrics:**
   - `cpu_allocated`: Number of CPUs allocated
   - `cpu_usage_peak`: Peak CPU usage during boost period
   - `cpu_usage_post_boost`: CPU usage after restoration
   - `memory_used`: Memory consumption

3. **System Metrics:**
   - `other_containers_affected`: Impact on concurrent containers
   - `agent_cpu_usage`: Total agent CPU usage
   - `restoration_success`: Whether CPU was successfully restored

### Test Execution Script

```bash
#!/bin/bash
# test_cpu_boost.sh

set -e

RESULTS_DIR="./cpu-boost-results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# Test configurations
CONFIGS=(
    "false:1.0:0:baseline"
    "true:1.5:30:boost-1.5x"
    "true:2.0:60:boost-2x"
    "true:3.0:60:boost-3x"
    "true:5.0:120:boost-5x"
)

# Test cases (name:image:script)
TEST_CASES=(
    "pytorch:pytorch/pytorch:latest:tests/pytorch_load_test.py"
    "tensorflow:tensorflow/tensorflow:latest:tests/tensorflow_load_test.py"
    "java:openjdk:11:tests/java_load_test/LoadTest.java"
    "julia:julia:latest:tests/julia_load_test.jl"
    "scipy:jupyter/scipy-notebook:latest:tests/scipy_load_test.py"
    "nodejs:node:18:tests/nodejs_load_test/test.js"
    "baseline:python:3.11-slim:tests/baseline_test.py"
)

# Run tests
for test_case in "${TEST_CASES[@]}"; do
    IFS=':' read -r name image script <<< "$test_case"
    echo "========================================"
    echo "Testing: $name ($image)"
    echo "========================================"

    for config in "${CONFIGS[@]}"; do
        IFS=':' read -r enabled factor duration config_name <<< "$config"

        echo "  Config: $config_name (enabled=$enabled, factor=$factor, duration=$duration)"

        # Update agent configuration
        cat > /tmp/agent.toml <<EOF
[container]
cpu-boost-enabled = $enabled
cpu-boost-factor = $factor
cpu-boost-duration = $duration
EOF

        # Restart agent with new config
        sudo systemctl restart backendai-agent
        sleep 5

        # Run test (repeat 3 times for statistical significance)
        for run in {1..3}; do
            echo "    Run $run/3..."

            result_file="$RESULTS_DIR/${name}_${config_name}_run${run}.json"

            # Execute test
            ./backend.ai run \
                --image="$image" \
                --cpus=2 \
                --mem=4g \
                "$script" > "$result_file" 2>&1

            # Parse metrics from output
            grep "METRICS_JSON" -A 50 "$result_file" | \
                tail -n +2 | \
                jq '.' > "${result_file}.metrics.json"

            sleep 10  # Cool-down period
        done
    done
done

echo "========================================"
echo "All tests completed!"
echo "Results saved to: $RESULTS_DIR"
echo "========================================"

# Generate summary report
python3 generate_report.py "$RESULTS_DIR"
```

### Report Generation Script

```python
#!/usr/bin/env python3
# generate_report.py

import json
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def load_results(results_dir):
    """Load all test results from directory."""
    results = []
    for metrics_file in Path(results_dir).glob("*.metrics.json"):
        with open(metrics_file) as f:
            data = json.load(f)
            # Parse filename: {test}_{config}_run{N}.json.metrics.json
            parts = metrics_file.stem.replace('.json', '').split('_')
            data['test_case'] = parts[0]
            data['config'] = parts[1]
            data['run'] = int(parts[2].replace('run', ''))
            results.append(data)
    return pd.DataFrame(results)

def calculate_improvement(df):
    """Calculate improvement vs baseline."""
    baseline = df[df['config'] == 'baseline'].groupby('test_case')['total_time'].mean()

    improvements = []
    for config in df['config'].unique():
        if config == 'baseline':
            continue
        config_times = df[df['config'] == config].groupby('test_case')['total_time'].mean()
        improvement = ((baseline - config_times) / baseline * 100).to_dict()
        for test_case, pct in improvement.items():
            improvements.append({
                'test_case': test_case,
                'config': config,
                'improvement_pct': pct,
                'baseline_time': baseline[test_case],
                'boosted_time': config_times[test_case],
            })
    return pd.DataFrame(improvements)

def generate_report(results_dir):
    """Generate comprehensive test report."""
    df = load_results(results_dir)
    improvements = calculate_improvement(df)

    # Summary statistics
    print("=" * 80)
    print("CPU BOOST TEST RESULTS SUMMARY")
    print("=" * 80)
    print()

    print("Average Improvement by Configuration:")
    print("-" * 80)
    summary = improvements.groupby('config')['improvement_pct'].agg(['mean', 'std', 'min', 'max'])
    print(summary.to_string())
    print()

    print("Improvement by Test Case (2x boost):")
    print("-" * 80)
    boost_2x = improvements[improvements['config'] == 'boost-2x'].sort_values('improvement_pct', ascending=False)
    print(boost_2x[['test_case', 'improvement_pct', 'baseline_time', 'boosted_time']].to_string(index=False))
    print()

    # Generate plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Plot 1: Improvement by test case
    ax1 = axes[0, 0]
    boost_2x_sorted = boost_2x.sort_values('improvement_pct')
    ax1.barh(boost_2x_sorted['test_case'], boost_2x_sorted['improvement_pct'])
    ax1.set_xlabel('Improvement (%)')
    ax1.set_title('CPU Boost Improvement by Test Case (2x factor)')
    ax1.axvline(x=0, color='red', linestyle='--', linewidth=0.5)

    # Plot 2: Time comparison
    ax2 = axes[0, 1]
    x = range(len(boost_2x_sorted))
    width = 0.35
    ax2.bar([i - width/2 for i in x], boost_2x_sorted['baseline_time'], width, label='Baseline')
    ax2.bar([i + width/2 for i in x], boost_2x_sorted['boosted_time'], width, label='Boosted (2x)')
    ax2.set_ylabel('Time (seconds)')
    ax2.set_title('Loading Time: Baseline vs Boosted')
    ax2.set_xticks(x)
    ax2.set_xticklabels(boost_2x_sorted['test_case'], rotation=45, ha='right')
    ax2.legend()

    # Plot 3: Improvement by config
    ax3 = axes[1, 0]
    config_avg = improvements.groupby('config')['improvement_pct'].mean().sort_values()
    ax3.barh(config_avg.index, config_avg.values)
    ax3.set_xlabel('Average Improvement (%)')
    ax3.set_title('Average Improvement by Boost Configuration')

    # Plot 4: Distribution
    ax4 = axes[1, 1]
    for config in improvements['config'].unique():
        data = improvements[improvements['config'] == config]['improvement_pct']
        ax4.hist(data, alpha=0.5, label=config, bins=10)
    ax4.set_xlabel('Improvement (%)')
    ax4.set_ylabel('Frequency')
    ax4.set_title('Distribution of Improvements')
    ax4.legend()

    plt.tight_layout()
    plt.savefig(f"{results_dir}/summary_plots.png", dpi=300)
    print(f"Plots saved to: {results_dir}/summary_plots.png")

    # Save detailed CSV
    improvements.to_csv(f"{results_dir}/improvements.csv", index=False)
    df.to_csv(f"{results_dir}/raw_results.csv", index=False)
    print(f"CSV files saved to: {results_dir}/")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <results_dir>")
        sys.exit(1)

    generate_report(sys.argv[1])
```

---

## Side Effect Verification

### 1. Concurrent Container Impact Test

**Objective:** Measure if CPU boost affects other containers starting simultaneously.

**Test Script:** `tests/concurrent_start_test.sh`
```bash
#!/bin/bash

echo "Testing concurrent container starts..."

# Configuration: 2x boost, 60s duration
cat > /tmp/agent.toml <<EOF
[container]
cpu-boost-enabled = true
cpu-boost-factor = 2.0
cpu-boost-duration = 60
EOF

sudo systemctl restart backendai-agent
sleep 5

# Start 5 containers simultaneously
echo "Starting 5 PyTorch containers simultaneously..."
for i in {1..5}; do
    (
        start=$(date +%s.%N)
        ./backend.ai run \
            --image=pytorch/pytorch:latest \
            --cpus=2 \
            --mem=4g \
            tests/pytorch_load_test.py > "/tmp/concurrent_${i}.log" 2>&1
        end=$(date +%s.%N)
        duration=$(echo "$end - $start" | bc)
        echo "Container $i completed in ${duration}s"
    ) &
done

wait

echo "All containers completed!"

# Analyze results
echo "Individual completion times:"
for i in {1..5}; do
    time=$(grep "total_time" "/tmp/concurrent_${i}.log" | grep -oP '\d+\.\d+')
    echo "  Container $i: ${time}s"
done
```

**Expected Behavior:**
- All containers should complete within reasonable time
- No container should be starved of CPU
- Total agent CPU usage should not exceed 100% for extended periods

### 2. Memory Pressure Test

**Objective:** Verify CPU boost doesn't cause memory issues.

**Test Script:** `tests/memory_pressure_test.py`
```python
#!/usr/bin/env python3
import psutil
import time
import json

# Monitor system resources during heavy test
print("Monitoring system resources...")

metrics = []
for i in range(120):  # Monitor for 2 minutes
    metrics.append({
        'timestamp': time.time(),
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'memory_percent': psutil.virtual_memory().percent,
        'swap_percent': psutil.swap_memory().percent,
    })
    time.sleep(1)

# Check for anomalies
high_swap = [m for m in metrics if m['swap_percent'] > 10]
if high_swap:
    print(f"WARNING: High swap usage detected in {len(high_swap)} samples")

high_mem = [m for m in metrics if m['memory_percent'] > 90]
if high_mem:
    print(f"WARNING: High memory usage detected in {len(high_mem)} samples")

print(json.dumps({
    'avg_cpu': sum(m['cpu_percent'] for m in metrics) / len(metrics),
    'avg_memory': sum(m['memory_percent'] for m in metrics) / len(metrics),
    'max_memory': max(m['memory_percent'] for m in metrics),
    'samples_with_swap': len(high_swap),
}, indent=2))
```

### 3. CPU Restoration Verification

**Objective:** Confirm CPU is properly restored after boost period.

**Test Script:** `tests/cpu_restoration_test.py`
```python
#!/usr/bin/env python3
import time
import numpy as np
import json

print("Testing CPU restoration...")

# Continuous workload for 120 seconds
results = []
for i in range(120):
    start = time.time()

    # CPU-intensive task
    A = np.random.randn(500, 500)
    result = np.linalg.eig(A)

    duration = time.time() - start
    results.append({
        'second': i,
        'duration': duration,
    })

    print(f"Second {i:3d}: {duration:.3f}s")

    time.sleep(max(0, 1 - duration))  # Try to maintain 1 second intervals

# Analyze before/after boost
before_boost = results[:30]  # First 30 seconds
after_boost = results[70:]   # After 60s + 10s buffer

avg_before = sum(r['duration'] for r in before_boost) / len(before_boost)
avg_after = sum(r['duration'] for r in after_boost) / len(after_boost)

print(json.dumps({
    'avg_duration_before_boost': avg_before,
    'avg_duration_after_boost': avg_after,
    'slowdown_factor': avg_after / avg_before,
    'expected_slowdown': 2.0,  # Should match boost factor
}, indent=2))

if avg_after / avg_before > 2.5:
    print("WARNING: Performance degradation exceeds expected boost factor!")
```

---

## Expected Results Summary

### High-Impact Cases (>30% improvement expected)
- ✅ PyTorch: Heavy C++ extension loading
- ✅ TensorFlow: CUDA initialization
- ✅ Julia: Extensive JIT compilation

### Medium-Impact Cases (15-30% improvement)
- ✅ Java: JVM initialization and class loading
- ✅ Scientific Python: Multiple C extensions
- ✅ Backend.AI images: Combined frameworks

### Low-Impact Cases (<15% improvement)
- ✅ Node.js: Primarily I/O bound
- ✅ Lightweight Python: Minimal initialization

### Side Effects to Monitor
- ⚠️ CPU contention with concurrent containers
- ⚠️ Memory pressure during boost period
- ⚠️ Proper CPU restoration after timeout
- ⚠️ Agent stability under high load

---

## Recommendations Based on Expected Results

### If improvement is >25%:
- **Deploy to production** with conservative settings (1.5-2x factor, 30-60s duration)
- Enable for compute-intensive images only
- Monitor agent CPU usage closely

### If improvement is 10-25%:
- **Conditionally enable** based on user tier or workload type
- Use shorter duration (30s) to minimize side effects
- Consider per-image configuration

### If improvement is <10%:
- **Re-evaluate** the feature or adjust implementation
- Consider alternative optimizations (image layer caching, etc.)
- May still be valuable for specific high-value workloads

---

## Next Steps

1. **Prepare test environment:**
   ```bash
   # Install test dependencies
   pip install pandas matplotlib numpy scipy

   # Prepare test scripts
   chmod +x tests/*.sh tests/*.py
   ```

2. **Run baseline tests** (no boost):
   ```bash
   ./test_cpu_boost.sh baseline
   ```

3. **Run boost tests** with different configurations:
   ```bash
   ./test_cpu_boost.sh all
   ```

4. **Analyze results:**
   ```bash
   python3 generate_report.py ./cpu-boost-results/latest
   ```

5. **Verify side effects:**
   ```bash
   ./tests/concurrent_start_test.sh
   python3 tests/memory_pressure_test.py
   python3 tests/cpu_restoration_test.py
   ```

6. **Make decision** based on data and recommendations above.

---

## Questions to Answer

After testing, we should be able to answer:

- ✅ Which workloads benefit most from CPU boost?
- ✅ What is the optimal boost factor and duration?
- ✅ Are there negative side effects on concurrent containers?
- ✅ Does the feature justify the added complexity?
- ✅ Should this be enabled by default or opt-in?
- ✅ Are there specific images that should have boost disabled?

Good luck with testing! 🚀
