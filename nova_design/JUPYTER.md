# Nova Jupyter Integration

Nova provides a first-class experience in Jupyter environments, designed to feel native to data scientists while providing modern language benefits.

## 1. The Nova Kernel

The Nova Kernel is a thin wrapper around the **IPython** kernel. It intercepts cells containing Nova code, transpiles them to Python on-the-fly, and executes them within the standard IPython environment.

- **Magics Compatibility**: All standard IPython magics (e.g., `%timeit`, `%matplotlib inline`) are supported. The Nova parser identifies lines starting with `%` or `!!` and preserves them during transpilation.
- **Incremental State**: Variables defined in one cell are available in subsequent cells, maintaining the familiar notebook workflow.

## 2. AI-Enhanced Notebook Features

- **Error Explainer**: When a cell execution fails, Nova provides a "Explain with AI" button that uses an LLM to analyze the Nova code, the transpiled Python, and the traceback to provide a clear explanation and a suggested fix.
- **Inline Visualization**: Nova's `viz` library is optimized for Jupyter, automatically rendering interactive Plotly or Bokeh charts directly in the output cell.
- **Prompt Execution**: Cells starting with `/?` allow for natural language instructions that Nova's integrated AI converts into Nova code.
  - Example cell: `/? Load the iris dataset and show the correlation heatmap.`

## 3. Native Notebook Syntax

Nova notebooks (`.nvnb`) use the same format as standard `.ipynb` files but contain Nova code. The Jupyter extension for Nova provides syntax highlighting, autocomplete, and live linting for Nova syntax within the cells.

## 4. Environment Detection

The Nova kernel automatically detects the active environment (Conda, Venv, or Poetry) and ensures that the correct Python interpreter and libraries are used. It also auto-detects GPU availability and displays a status indicator in the Jupyter toolbar.
