# AI - server setup
> Note : we are going to use macbook m4 for deploying vlm

For now we are going to use  **Qwen-3.5-9B-MLX-4bit**  - `mlx-community/Qwen3.5-9B-MLX-4bit` from huggingface.

This is the model currently being tested and performing well on prescriptions so we are going to use this model.

## Prerequisites
#### 1. Huggingface account and hf cli setup
   - create Huggingface account
   - Install huggingface-cli
     ```
     brew install hf
     ```
     ```
     hf auth login
     ```
     for detailed setup of `hf cli` refer [click here](https://huggingface.co/docs/huggingface_hub/en/guides/cli#hf-auth-login)
#### 2. uv setup
   
   An extremely fast Python package and project manager, written in Rust.
   [Install and setup uv](https://docs.astral.sh/uv/getting-started/installation/)

   - required `python version : 3.11.14`
   - create a virtual environment
   ```
   uv venv --python 3.11.14 mlx-vlm
   ```
   activate the environment
   ```
   source mlx-vlm/bin/activate
   ```

#### 3. MLX-VLM

   
   MLX-VLM is a package for inference and fine-tuning of Vision Language Models (VLMs) and Omni Models (VLMs with audio and video support) on your Mac using MLX.
   - ```
     uv pip install git+https://github.com/Blaizzy/mlx-vlm.git
     ```
### TO run the model
```
mlx_vlm.generate \
  --model mlx-community/Qwen3.5-9B-MLX-4bit \
  --prompt "Extract the every text from the doctor prescription and give the output in json format" \
  --image ~/mediscan-iot/data/prescriptions/pr-2.png \
  --max-tokens 10000
```
