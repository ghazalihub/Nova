# Nova AI-First Standard Library Design

The Nova Standard Library (NSL) is designed to provide a unified, intuitive, and high-performance interface for AI and Data Science, built on top of the industry-standard Python libraries.

## 1. Core Modules

### `nova.ai` (Neural Networks & Tensors)
Wraps **PyTorch** and **TensorFlow** seamlessly.

- **`Tensor`**: The primary data structure.
  - `let t = Tensor.randn([3, 224, 224])`
  - Automatic conversion to/from NumPy/Torch/Jax.
- **`Model`**: Base class for all neural networks.
  - Built-in `train()`, `evaluate()`, `predict()` methods.
  - Automatic parameter tracking.
- **`layers`**: Common NN layers.
  - `layers.Dense(units=128, activation="relu")`
- **`losses` & `optimizers`**:
  - `losses.CrossEntropy()`
  - `optimizers.Adam(learning_rate=1e-3)`

### `nova.data` (Data Manipulation)
Wraps **Pandas** and **Polars**.

- **`DataFrame`**: High-level data table.
  - Lazy evaluation by default for large datasets.
  - SQL-like interface: `df.select("age").where(df.age > 18)`.
- **`Dataset`**: Abstraction for ML data.
  - Supports local files, S3, GCS, and Azure Blob.
  - `Dataset.from_csv("data/*.csv").shuffle().batch(32)`.
- **`Validation`**: Built-in data quality checks.
  - `df.validate({ "age": v.range(0, 120), "email": v.is_email() })`.

### `nova.viz` (Visualization)
Wraps **Matplotlib**, **Seaborn**, and **Plotly**.

- **`plot`**: Simple plotting.
  - `viz.plot(x, y, type="scatter")`.
- **`Dashboard`**: Declarative UI for data apps.
  - `Dashboard { Text("Title"); Plot(df); }`.
- **`Theme`**: Universal theming engine.

### `nova.hardware` (Hardware Acceleration)
Wraps **CUDA**, **MPS**, and **ROCm**.

- **Auto-detection**: Nova automatically detects the best available hardware (NVIDIA GPU, Apple Silicon, etc.).
- **`Device`**: Explicit control when needed.
  - `with (hardware.gpu(0)) { ... }`.
- **Memory Management**: Automatic tensor migration between CPU and GPU.

### `nova.exp` (Experiment Tracking)
Wraps **MLflow** and **Weights & Biases**.

- **`Run`**: Context manager for experiments.
  - `exp.start_run("experiment_name") { exp.log_metric("acc", 0.95); }`.
- **`Registry`**: Versioning for models and datasets.

---

## 2. Declarative Training Loops

Nova replaces hundreds of lines of boilerplate with a single declarative call.

```nova
import { Model, layers, optimizers } from "nova.ai";
import { Dataset } from "nova.data";

const model = Model({
    layers: [
        layers.Conv2D(32, 3),
        layers.Flatten(),
        layers.Dense(10)
    ]
});

const data = Dataset.load("mnist");

model.fit(data, {
    optimizer: optimizers.Adam(),
    epochs: 10,
    callbacks: [callbacks.EarlyStopping(patience=3)]
});
```

## 3. Seamless Interoperability

Every NSL object can be converted to its underlying Python counterpart at zero cost.

- `tensor.to_torch()` -> `torch.Tensor`
- `dataframe.to_pandas()` -> `pandas.DataFrame`
- `model.to_jax()` -> `jax.nn.Module` (where applicable)

## 4. Automatic Vectorization & Parallelism

The NSL identifies patterns that can be vectorized and automatically applies them during transpilation to Python, often using `numpy` or `torch` vectorized operations instead of standard Python loops.

```nova
// Nova
let result = data.map(x => x * 2);

// Transpiled Python (Optimized)
import numpy as np
result = data_np * 2
```

## 5. Built-in Model Evaluation Pipelines

Nova includes a suite of evaluation tools:
- **`eval.classification_report(y_true, y_pred)`**
- **`eval.confusion_matrix(y_true, y_pred)`**
- **`eval.feature_importance(model, data)`**
- **`eval.explain_prediction(model, sample)`** (SHAP/LIME integration)
